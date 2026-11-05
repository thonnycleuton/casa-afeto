"""Gemini OCR client for M13.

Calls Google Gemini API to extract purchase document data from images.
Model and API key are configurable via environment variables (D-21).
"""

from __future__ import annotations

import json
import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.core.config import settings
from app.ocr.schemas import OCRDiscount, OCRItem, OCRResult

logger = logging.getLogger(__name__)

# Prompt template for Gemini OCR extraction.
OCR_PROMPT = """Você é um assistente de extração de dados de documentos de compra.
Analise a imagem e extraia os dados da nota fiscal ou documento de compra.

Retorne APENAS um JSON com esta estrutura:
{
  "document_total": (valor total do documento, se legível, caso contrário null),
  "purchased_at": "YYYY-MM-DD" (data do documento, se legível, caso contrário null),
  "access_key": "chave de acesso da nota fiscal, se legível, caso contrário null",
  "items": [
    {
      "description": "nome do produto",
      "quantity": quantidade (número),
      "commercial_unit": "unidade comercial (ex: UN, CX, FD), se presente",
      "commercial_unit_price": preço unitário (número),
      "subtotal_printed": subtotal impresso no documento (número, se disponível),
      "subtotal_calculated": quantidade × preço unitário (número),
      "discounts": [
        {
          "value": valor do desconto (número),
          "nature": "item" ou "grupo",
          "description": "descrição do desconto"
        }
      ]
    }
  ],
  "document_discounts": [
    {
      "value": valor do desconto (número),
      "nature": "documento",
      "description": "descrição do desconto"
    }
  ]
}

Regras importantes:
- Extraia SOMENTE o que está visível e legível no documento.
- NÃO invente valores, quantidades, preços ou nomes.
- Se um campo não estiver legível, use null.
- Preserve os valores numéricos com precisão.
- Não aplique descontos automaticamente — apenas identifique-os.
- Se não houver itens, retorne uma lista vazia.
"""


def _parse_decimal(value: object) -> Decimal | None:
    """Safely parse a JSON value to Decimal."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _parse_items(raw_items: list[dict]) -> list[OCRItem]:
    """Parse raw item dicts from Gemini response into OCRItem models."""
    import uuid

    items: list[OCRItem] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue

        # Generate stable item_id for each extracted item
        item_id = uuid.uuid4().hex

        description = raw.get("description")
        if isinstance(description, str):
            description = description.strip()
            if not description:
                description = None

        quantity = _parse_decimal(raw.get("quantity"))
        unit_price = _parse_decimal(raw.get("commercial_unit_price"))
        subtotal_printed = _parse_decimal(raw.get("subtotal_printed"))
        subtotal_calculated = _parse_decimal(raw.get("subtotal_calculated"))

        # Parse discounts
        discounts: list[OCRDiscount] = []
        for disc_raw in raw.get("discounts") or []:
            if isinstance(disc_raw, dict):
                disc = OCRDiscount(
                    value=_parse_decimal(disc_raw.get("value")),
                    nature=disc_raw.get("nature"),
                    item_id=item_id,
                    document_level=False,
                    description=disc_raw.get("description"),
                )
                discounts.append(disc)

        item = OCRItem(
            item_id=item_id,
            description=description,
            quantity=quantity,
            commercial_unit=raw.get("commercial_unit"),
            commercial_unit_price=unit_price,
            subtotal_printed=subtotal_printed,
            subtotal_calculated=subtotal_calculated,
            discounts=discounts,
        )
        items.append(item)
    return items


def _parse_document_discounts(raw_discounts: list[dict]) -> list[OCRDiscount]:
    """Parse document-level discounts from Gemini response."""
    discounts: list[OCRDiscount] = []
    for disc_raw in raw_discounts or []:
        if isinstance(disc_raw, dict):
            disc = OCRDiscount(
                value=_parse_decimal(disc_raw.get("value")),
                nature=disc_raw.get("nature", "documento"),
                item_id=None,
                document_level=True,
                description=disc_raw.get("description"),
            )
            discounts.append(disc)
    return discounts


def parse_gemini_response(text: str) -> OCRResult:
    """Parse the Gemini text response into an OCRResult.

    Extracts JSON from the response text and validates the structure.
    """
    # Try to find JSON in the response — Gemini may wrap it in markdown
    text = text.strip()
    if text.startswith("```"):
        # Remove markdown code fences
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1].strip()
            # Remove language identifier if present (e.g., "json\n{...}")
            if text.startswith("json"):
                text = text[4:].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Resposta do Gemini não é JSON válido: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Resposta do Gemini não é um objeto JSON")

    # Parse purchased_at
    purchased_at = None
    if data.get("purchased_at"):
        from datetime import datetime
        try:
            purchased_at = datetime.strptime(str(data["purchased_at"]), "%Y-%m-%d")
        except ValueError:
            logger.warning("Data do documento em formato inválido: %s", data.get("purchased_at"))

    # Parse items
    raw_items = data.get("items") or []
    items = _parse_items(raw_items) if isinstance(raw_items, list) else []

    # Parse document discounts
    raw_doc_discounts = data.get("document_discounts") or []
    document_discounts = _parse_document_discounts(raw_doc_discounts) if isinstance(raw_doc_discounts, list) else []

    return OCRResult(
        document_total=_parse_decimal(data.get("document_total")),
        purchased_at=purchased_at,
        access_key=data.get("access_key"),
        items=items,
        document_discounts=document_discounts,
    )


def call_gemini_ocr(image_path: Path, mime_type: str | None = None) -> OCRResult:
    """Call Gemini API to extract data from a purchase document image.

    Args:
        image_path: Path to the uploaded image file.
        mime_type: MIME type of the image (e.g. "image/jpeg", "image/png", "image/webp").
                   Defaults to "image/jpeg" if not provided.

    Returns:
        OCRResult with extracted data.

    Raises:
        RuntimeError: If the API call fails.
        ValueError: If the response cannot be parsed.
    """
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "google-genai não está instalado. Instale com: pip install google-genai"
        ) from exc

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não está configurado")

    model = settings.GEMINI_MODEL

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
    except OSError as exc:
        raise RuntimeError(f"Não foi possível ler o arquivo: {exc}") from exc

    # Use the actual MIME type of the uploaded file, defaulting to image/jpeg
    effective_mime = mime_type if mime_type else "image/jpeg"

    try:
        from google.genai import types

        response = client.models.generate_content(
            model=model,
            contents=[OCR_PROMPT, types.Part.from_bytes(data=image_data, mime_type=effective_mime)],
        )
    except Exception as exc:
        logger.error("Falha na chamada ao Gemini: %s", exc)
        raise RuntimeError(f"Falha ao processar com Gemini: {exc}") from exc

    text = response.text if hasattr(response, "text") else str(response)
    if not text.strip():
        raise ValueError("Resposta vazia do Gemini")

    logger.info("Gemini OCR concluído com modelo %s", model)
    return parse_gemini_response(text)
