"""Product matching service for M13 OCR.

Matches extracted item descriptions against registered products using
three criteria: exact normalized, substring, and fuzzy (D-19).
"""

from __future__ import annotations

import logging
import unicodedata
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.products.models import Product

logger = logging.getLogger(__name__)


def normalize_name(name: str) -> str:
    """Normalize a product name for comparison.

    Removes accents, converts to lowercase, and collapses whitespace.
    """
    # Remove accents
    nfkd = unicodedata.normalize("NFKD", name)
    no_accents = "".join(ch for ch in nfkd if not unicodedata.category(ch).startswith("M"))
    # Lowercase and collapse whitespace
    normalized = no_accents.lower().strip()
    return " ".join(normalized.split())


def exact_match(extracted: str, products: List[Product]) -> Optional[Product]:
    """Find exact normalized match."""
    extracted_norm = normalize_name(extracted)
    for product in products:
        if normalize_name(product.name) == extracted_norm:
            return product
    return None


def substring_match(extracted: str, products: List[Product]) -> List[Tuple[Product, int]]:
    """Find products whose normalized name contains the extracted name as substring.

    Returns list of (product, score) sorted by score descending.
    Score is based on how much of the product name is covered.
    """
    extracted_norm = normalize_name(extracted)
    if not extracted_norm:
        return []

    results: List[Tuple[Product, int]] = []
    for product in products:
        product_norm = normalize_name(product.name)
        if extracted_norm in product_norm:
            # Higher score for shorter matches (more specific)
            score = len(product_norm) - len(extracted_norm)
            results.append((product, score))

    results.sort(key=lambda x: x[1])
    return results


def _levenshtein_distance(a: str, b: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(a) < len(b):
        return _levenshtein_distance(b, a)

    if len(b) == 0:
        return len(a)

    previous_row = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        current_row = [i + 1]
        for j, cb in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (ca != cb)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def fuzzy_match(extracted: str, products: List[Product], threshold: float = 0.6) -> List[Tuple[Product, float]]:
    """Find products with similar names using Levenshtein similarity.

    Returns list of (product, similarity) sorted by similarity descending.
    Only returns products above the threshold.
    """
    extracted_norm = normalize_name(extracted)
    if not extracted_norm:
        return []

    results: List[Tuple[Product, float]] = []
    for product in products:
        product_norm = normalize_name(product.name)
        if not product_norm:
            continue

        # Calculate similarity
        max_len = max(len(extracted_norm), len(product_norm))
        if max_len == 0:
            continue

        distance = _levenshtein_distance(extracted_norm, product_norm)
        similarity = 1.0 - (distance / max_len)

        if similarity >= threshold:
            results.append((product, round(similarity, 3)))

    results.sort(key=lambda x: (-x[1], x[0].name))
    return results


class MatchSuggestion:
    """A product match suggestion with confidence level."""

    def __init__(
        self,
        product: Product,
        match_type: str,
        confidence: float,
    ) -> None:
        self.product = product
        self.match_type = match_type  # "exact", "substring", "fuzzy"
        self.confidence = confidence

    def to_dict(self) -> dict:
        return {
            "product_id": self.product.id,
            "product_name": self.product.name,
            "match_type": self.match_type,
            "confidence": self.confidence,
            "base_unit": self.product.base_unit,
            "commercial_conversion_factor": (
                str(self.product.commercial_conversion_factor)
                if self.product.commercial_conversion_factor is not None
                else None
            ),
        }


def match_products(
    extracted_description: str,
    db: Session,
) -> List[MatchSuggestion]:
    """Find matching products for an extracted item description.

    Uses three criteria in order: exact normalized, substring, fuzzy (D-19).
    Returns suggestions sorted by confidence.
    """
    products = list(db.scalars(select(Product).order_by(Product.name, Product.id)).all())

    suggestions: List[MatchSuggestion] = []
    seen_ids: set[int] = set()

    # 1. Exact normalized match
    exact = exact_match(extracted_description, products)
    if exact:
        suggestions.append(MatchSuggestion(exact, "exact", 1.0))
        seen_ids.add(exact.id)

    # 2. Substring match
    substring_results = substring_match(extracted_description, products)
    for product, score in substring_results[:5]:  # Limit to 5 suggestions
        if product.id not in seen_ids:
            # Confidence decreases with score (score = extra chars)
            confidence = max(0.5, 1.0 - (score * 0.05))
            suggestions.append(MatchSuggestion(product, "substring", round(confidence, 3)))
            seen_ids.add(product.id)

    # 3. Fuzzy match
    fuzzy_results = fuzzy_match(extracted_description, products)
    for product, similarity in fuzzy_results[:5]:
        if product.id not in seen_ids:
            suggestions.append(MatchSuggestion(product, "fuzzy", similarity))
            seen_ids.add(product.id)

    return suggestions
