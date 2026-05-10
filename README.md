# Alpha White ENEM Extractor

Microserviço FastAPI para extrair prova + gabarito do ENEM e retornar JSON padronizado para o Rails.

## Requisitos

- Python 3.11+
- Dependências em `requirements.txt`

## Rodando local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

- `GET /health` -> status do serviço.
- `POST /extract` -> multipart com:
  - `prova` (PDF da prova, ex: `2023_PV_impresso_D1_CD1.pdf`)
  - `gabarito` (PDF do gabarito, ex: `2023_GB_impresso_D1_CD1.pdf`)

## Contrato de resposta (`POST /extract`)

```json
{
  "exam": {
    "year": 2023,
    "day": "D1",
    "booklet_color": "CD1",
    "metadata": { "source": "inep_pdf_extractor" }
  },
  "questions": [
    {
      "number_in_exam": 1,
      "area": "LC",
      "skill": null,
      "statement": "...",
      "alternatives": ["A)...", "B)..."],
      "correct_letter": "A"
    }
  ]
}
```

## Observações

- O adapter usa o `EnemPDFextractor` existente e normaliza a saída para o formato esperado no Rails.
- Questões sem estrutura mínima podem ser descartadas na normalização.
- Anos com encoding irregular (ex.: 2020) podem ter menor qualidade de extração textual.
