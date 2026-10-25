#!/usr/bin/env python3
"""
validate_spec_casa.py - Validação de especificações no formato Casa Afeto.

Adaptado do validate_spec.py do TLC-Spec-Driven para validar o formato
de especificação usado em docs/milestones/<milestone>/specification.md.

O que verifica:
  ERROR  - Seção obrigatória ausente (Objetivo, Escopo, Fora do Escopo)
  ERROR  - Critério de aceitação sem palavra-chave testável (SHALL, deve, deve rejeitar)
  WARN   - Decisões pendentes não resolvidas
  WARN   - Assumptions sem justificativa

Uso:
  python3 scripts/tlc/validate_spec_casa.py docs/milestones/m5-payments/specification.md
  python3 scripts/tlc/validate_spec_casa.py docs/milestones/m5-payments/
  python3 scripts/tlc/validate_spec_casa.py --strict docs/milestones/m5-payments/

Exit codes: 0 pass, 1 errors found (or warnings under --strict), 2 usage error.
"""

import argparse
import os
import re
import sys

# Seções obrigatórias no formato Casa Afeto
# Cada entrada pode ser uma string simples ou uma tupla (nome_exibido, padrão_regex)
REQUIRED_SECTIONS = [
    ("Objetivo", r"(Objetivo|Finalidade|Propósito)"),
    "Escopo",
    ("Fora do Escopo", r"(Fora do Escopo|Explicitamente fora do escopo|Explicitamente Fora do Escopo|Out of Scope)"),
]

# Seções recomendadas (warning se ausentes)
RECOMMENDED_SECTIONS = [
    "Dependências",
    "Decisões Pendentes",
]

# Padrões para critérios de aceitação testáveis
TESTABLE_KEYWORDS = [
    r"\bshall\b",
    r"\bdeve\b",
    r"\bdeveria\b",
    r"\brejeita\b",
    r"\baceita\b",
    r"\bpermite\b",
    r"\bimpede\b",
    r"\bgarante\b",
    r"\bmanuten\b",
    r"\bpreserva\b",
    r"\bbloqueia\b",
    r"\blibera\b",
    r"\bregistra\b",
    r"\bcalcula\b",
    r"\bverifica\b",
    r"\btransiciona\b",
    r"\bautoriza\b",
]

# Padrões Given/When/Then (Gherkin-like)
GHERKIN_PATTERN = re.compile(r"(given|when|then|dado|quando|então)", re.IGNORECASE)

# IDs de regra de negócio (ex: PAY-001, RES-001)
RULE_ID_RE = re.compile(r"^[A-Z]{2,5}-\d{3,4}$")


def resolve_spec(target):
    """Retorna o caminho para specification.md a partir de um arquivo ou diretório."""
    if os.path.isfile(target):
        return target
    if os.path.isdir(target):
        cand = os.path.join(target, "specification.md")
        if os.path.isfile(cand):
            return cand
        # Tenta spec.md como fallback
        cand = os.path.join(target, "spec.md")
        if os.path.isfile(cand):
            return cand
    return None


def section_bounds(lines, name):
    """Retorna (start, end) dos índices das linhas de uma seção ## name.
    
    name pode ser uma string simples ou uma tupla (nome_exibido, padrão_regex).
    """
    if isinstance(name, tuple):
        pattern = name[1]  # regex pattern
    else:
        pattern = re.escape(name)
    
    start = None
    for i, ln in enumerate(lines):
        # Match ## N. Name ou ## N.M. Name ou ## Name
        # Accepts: "1.", "2.2", "3.1.2" followed by space
        if re.match(r"^#{1,3}\s+(?:(\d+(?:\.\d+)*(?:\.\s+|\s+)))?" + pattern + r"\s*$", ln.strip()):
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        if re.match(r"^#{1,3}\s+\S", lines[j]):
            end = j
            break
    return (start, end)


def has_testable_keyword(text):
    """Verifica se um texto contém palavra-chave testável."""
    for kw in TESTABLE_KEYWORDS:
        if re.search(kw, text, re.IGNORECASE):
            return True
    return False


def check(spec_path):
    """Executa os checks de validação na especificação."""
    with open(spec_path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    errors = []
    warnings = []

    # 1. Seções obrigatórias
    for name in REQUIRED_SECTIONS:
        display_name = name[0] if isinstance(name, tuple) else name
        if section_bounds(lines, name) is None:
            errors.append(f"seção obrigatória ausente: ## {display_name}")

    # 2. Seções recomendadas
    for name in RECOMMENDED_SECTIONS:
        if section_bounds(lines, name) is None:
            warnings.append(f"seção recomendada ausente: ## {name}")

    # 3. Critérios de aceitação no arquivo acceptance-criteria.md
    ac_path = os.path.join(os.path.dirname(spec_path), "acceptance-criteria.md")
    if os.path.isfile(ac_path):
        errors_ac, warnings_ac = check_acceptance_criteria(ac_path)
        errors.extend(errors_ac)
        warnings.extend(warnings_ac)
    else:
        warnings.append("acceptance-criteria.md não encontrado no diretório do milestone")

    # 4. Decisões pendentes não resolvidas
    b = section_bounds(lines, "Decisões Pendentes")
    if b:
        pending_count = 0
        for i in range(*b):
            line = lines[i].strip()
            # Conta itens numerados que não estão marcados como resolvidos
            if re.match(r"^\d+\.\s+", line) and "✓" not in line and "Resolvido" not in line:
                pending_count += 1
        if pending_count > 0:
            warnings.append(f"{pending_count} decisão(ões) pendente(s) não resolvida(s)")

    # 5. Verifica referências a regras de negócio
    rule_ids = re.findall(r"\b([A-Z]{2,5}-\d{3,4})\b", text)
    if rule_ids:
        unique_rules = set(rule_ids)
        for rule_id in unique_rules:
            if not RULE_ID_RE.match(rule_id):
                warnings.append(f"ID de regra de negócio possivelmente inválido: {rule_id}")

    return errors, warnings


def check_acceptance_criteria(ac_path):
    """Valida o arquivo acceptance-criteria.md."""
    with open(ac_path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    errors = []
    warnings = []

    ac_count = 0
    testable_count = 0
    gherkin_count = 0
    tagged_count = 0
    frontend_ac_count = 0
    backend_frontend_ac_count = 0
    has_frontend_section = False

    # Check for ## Frontend section
    for ln in lines:
        if re.match(r"^##\s+Frontend\s*$", ln.strip(), re.IGNORECASE):
            has_frontend_section = True
            break

    for i, ln in enumerate(lines, start=1):
        stripped = ln.strip()

        # Detecta critérios de aceitação (headings ### AC-*)
        ac_heading_match = re.match(r"^#{2,4}\s+AC-[A-Z]+-\d+\s*(.*)$", stripped)
        if ac_heading_match:
            rest = ac_heading_match.group(1).strip()

            # Check for [Frontend] or [Backend + Frontend] tags
            if "[Frontend]" in rest:
                frontend_ac_count += 1
                tagged_count += 1
            elif "[Backend + Frontend]" in rest:
                backend_frontend_ac_count += 1
                tagged_count += 1
            elif "[Backend]" in rest:
                tagged_count += 1

        # Detecta critérios de aceitação (itens numerados ou list items com conteúdo)
        m = re.match(r"^\s*(\d+[.)]\s+|- \[.\] )(.+)$", ln)
        if m:
            content = m.group(2).strip()

            # Ignora linhas vazias ou placeholders
            if not content or re.match(r"^\[.*\]$", content):
                continue

            ac_count += 1

            # Verifica se é testável
            if has_testable_keyword(content):
                testable_count += 1

            # Verifica se usa formato Given/When/Then
            if GHERKIN_PATTERN.search(content):
                gherkin_count += 1

    # Frontend guardrails
    total_frontend_acs = frontend_ac_count + backend_frontend_ac_count
    if total_frontend_acs > 0 and not has_frontend_section:
        errors.append(
            f"{total_frontend_acs} critério(s) de aceitação com tag [Frontend] ou [Backend + Frontend] "
            f"encontrado(s), mas nenhuma seção '## Frontend' no acceptance-criteria.md — "
            f"o frontend pode ser esquecido ao fechar o milestone"
        )
    elif has_frontend_section and frontend_ac_count == 0:
        # Frontend section exists but no [Frontend] ACs found — might be untagged
        # Check if there are ACs inside the frontend section
        frontend_section_acs = 0
        in_frontend = False
        for ln in lines:
            if re.match(r"^##\s+Frontend\s*$", ln.strip(), re.IGNORECASE):
                in_frontend = True
                continue
            elif re.match(r"^##\s+\S", ln.strip()):
                in_frontend = False
                continue
            if in_frontend and re.match(r"^#{2,4}\s+AC-", ln.strip()):
                frontend_section_acs += 1
        if frontend_section_acs == 0:
            warnings.append(
                "Seção '## Frontend' existe mas não contém critérios de aceitação — "
                "verifique se os ACs de frontend estão presentes"
            )

    # Tag warnings
    total_acs = ac_count + frontend_ac_count + backend_frontend_ac_count + tagged_count
    if total_acs > 0 and tagged_count < total_acs:
        untagged = total_acs - tagged_count
        warnings.append(
            f"{untagged} critério(s) de aceitação sem tag [Backend]/[Frontend] — "
            f"tags ajudam a detectar omissão de frontend"
        )

    if ac_count > 0:
        testable_ratio = testable_count / ac_count * 100
        gherkin_ratio = gherkin_count / ac_count * 100

        if testable_ratio < 50:
            errors.append(
                f"apenas {testable_ratio:.0f}% dos {ac_count} critérios têm palavra-chave testável "
                f"(recomendado: ≥50%)"
            )
        elif testable_ratio < 80:
            warnings.append(
                f"{testable_ratio:.0f}% dos {ac_count} critérios têm palavra-chave testável "
                f"(ideal: ≥80%)"
            )

        if gherkin_ratio < 30:
            warnings.append(
                f"apenas {gherkin_ratio:.0f}% dos critérios usam formato Given/When/Then "
                f"(recomendado para clareza)"
            )

    return errors, warnings


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="validate_spec_casa.py",
        description="Validação de especificações no formato Casa Afeto."
    )
    p.add_argument("target", nargs="?", default=None, help="Caminho para specification.md ou diretório do milestone")
    p.add_argument("--strict", action="store_true", help="Trata warnings como erros")
    args = p.parse_args(argv)

    if not args.target:
        print("validate_spec_casa: passe um caminho para specification.md ou diretório do milestone.", file=sys.stderr)
        return 2

    spec = resolve_spec(args.target)
    if not spec:
        print(f"validate_spec_casa: specification.md não encontrado em {args.target}", file=sys.stderr)
        return 2

    errors, warnings = check(spec)

    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ERROR {e}")

    fail = errors or (warnings and args.strict)
    print(f"\nvalidate_spec_casa: {len(errors)} erro(s), {len(warnings)} alerta(s) em {spec}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
