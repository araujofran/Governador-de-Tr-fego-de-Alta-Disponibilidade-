import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

logger = logging.getLogger("TrafficController.FinOpsEngine")

@dataclass
class PricingModel:
    provider: str
    model: str
    input_price_per_million: float
    output_price_per_million: float
    cached_price_per_million: float = 0.0
    reasoning_price_per_million: float = 0.0
    currency: str = "USD"
    pricing_version: str = "v2026.09.05"
    source: str = "Official Commercial Pricing"

@dataclass
class UsageCostResult:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    reasoning_tokens: int
    total_tokens: int
    actual_cost_usd: float
    equivalent_cost_usd: float
    savings_usd: float
    usd_brl_rate: float
    actual_cost_brl: float
    equivalent_cost_brl: float
    savings_brl: float
    pricing_version: str
    price_status: str  # "CALCULATED" or "PRICE_NOT_AVAILABLE"

class FinOpsEngine:
    """
    Motor de Cálculo FinOps para LLMs (Camada FinOps & Capacity Planning).
    Converte consumo técnico de tokens (input vs. output) em indicadores financeiros.
    """

    DEFAULT_PRICING = {
        ("google", "gemini-3.6-flash"): PricingModel("google", "gemini-3.6-flash", 0.75, 3.75, 0.1875),
        ("google", "gemini-flash-latest"): PricingModel("google", "gemini-flash-latest", 0.75, 3.75, 0.1875),
        ("groq", "groq/compound-mini"): PricingModel("groq", "groq/compound-mini", 0.15, 0.60),
        ("groq", "openai/gpt-oss-120b"): PricingModel("groq", "openai/gpt-oss-120b", 0.15, 0.60),
        ("groq", "openai/gpt-oss-20b"): PricingModel("groq", "openai/gpt-oss-20b", 0.075, 0.30),
        ("openrouter", "minimax/minimax-m3"): PricingModel("openrouter", "minimax/minimax-m3", 0.20, 1.10)
    }

    DEFAULT_FX_RATE = 5.1262  # USD -> BRL cotação oficial 05/09/2026

    def __init__(self, fx_rate: float = DEFAULT_FX_RATE):
        self.fx_rate = fx_rate
        self.pricing_catalog = dict(self.DEFAULT_PRICING)

    def calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        reasoning_tokens: int = 0,
        is_free_tier: bool = True
    ) -> UsageCostResult:
        
        provider_key = provider.lower()
        key = (provider_key, model.lower())
        
        pricing = self.pricing_catalog.get(key)
        if not pricing:
            # Fallback para busca genérica por provider
            for (p, m), pr in self.pricing_catalog.items():
                if p == provider_key:
                    pricing = pr
                    break

        total_tokens = input_tokens + output_tokens + cached_tokens + reasoning_tokens

        if not pricing:
            return UsageCostResult(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_tokens=cached_tokens,
                reasoning_tokens=reasoning_tokens,
                total_tokens=total_tokens,
                actual_cost_usd=0.0,
                equivalent_cost_usd=0.0,
                savings_usd=0.0,
                usd_brl_rate=self.fx_rate,
                actual_cost_brl=0.0,
                equivalent_cost_brl=0.0,
                savings_brl=0.0,
                pricing_version="UNKNOWN",
                price_status="PRICE_NOT_AVAILABLE"
            )

        # Cálculo Granular Separado por Categoria de Token
        input_cost_usd = (input_tokens / 1_000_000.0) * pricing.input_price_per_million
        output_cost_usd = (output_tokens / 1_000_000.0) * pricing.output_price_per_million
        cached_cost_usd = (cached_tokens / 1_000_000.0) * pricing.cached_price_per_million
        reasoning_cost_usd = (reasoning_tokens / 1_000_000.0) * pricing.reasoning_price_per_million

        equivalent_cost_usd = input_cost_usd + output_cost_usd + cached_cost_usd + reasoning_cost_usd
        actual_cost_usd = 0.0 if is_free_tier else equivalent_cost_usd
        savings_usd = max(0.0, equivalent_cost_usd - actual_cost_usd)

        equivalent_cost_brl = equivalent_cost_usd * self.fx_rate
        actual_cost_brl = actual_cost_usd * self.fx_rate
        savings_brl = savings_usd * self.fx_rate

        return UsageCostResult(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
            total_tokens=total_tokens,
            actual_cost_usd=round(actual_cost_usd, 6),
            equivalent_cost_usd=round(equivalent_cost_usd, 6),
            savings_usd=round(savings_usd, 6),
            usd_brl_rate=self.fx_rate,
            actual_cost_brl=round(actual_cost_brl, 4),
            equivalent_cost_brl=round(equivalent_cost_brl, 4),
            savings_brl=round(savings_brl, 4),
            pricing_version=pricing.pricing_version,
            price_status="CALCULATED"
        )

    def calculate_capacity_projections(
        self,
        avg_input_tokens_per_call: float,
        avg_output_tokens_per_call: float,
        pricing: Optional[PricingModel] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Gera projeções financeiras para 1.000, 5.000, 10.000 e 50.000 atendimentos/mês."""
        if not pricing:
            pricing = self.DEFAULT_PRICING[("google", "gemini-3.6-flash")]

        scales = [1000, 5000, 10000, 50000]
        projections = {}

        for scale in scales:
            total_input = avg_input_tokens_per_call * scale
            total_output = avg_output_tokens_per_call * scale
            
            in_cost = (total_input / 1_000_000.0) * pricing.input_price_per_million
            out_cost = (total_output / 1_000_000.0) * pricing.output_price_per_million
            eq_usd = in_cost + out_cost
            eq_brl = eq_usd * self.fx_rate

            projections[f"{scale}_calls"] = {
                "monthly_calls": scale,
                "projected_input_tokens": int(total_input),
                "projected_output_tokens": int(total_output),
                "projected_total_tokens": int(total_input + total_output),
                "equivalent_cost_usd": round(eq_usd, 2),
                "equivalent_cost_brl": round(eq_brl, 2),
                "cost_per_call_brl": round(eq_brl / scale, 4)
            }

        return projections
