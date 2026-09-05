import time
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live

from rate_limiter import QuotaSnapshot
from finops_engine import FinOpsEngine

@dataclass
class TelemetryStats:
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    retried_tasks: int = 0
    count_429: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    start_time: float = field(default_factory=time.time)
    
    # Active limits state
    rem_rpm: int = 0
    rem_tpm: int = 0
    rpm_reset_sec: float = 0.0
    tpm_reset_sec: float = 0.0
    active_workers: int = 0
    current_status: str = "Iniciando..."
    recent_events: List[str] = field(default_factory=list)
    provider_snapshots: Dict[str, QuotaSnapshot] = field(default_factory=dict)

    # FinOps Realtime Cumulative State
    actual_cost_brl: float = 0.0
    equivalent_cost_brl: float = 0.0
    savings_brl: float = 0.0

class TelemetryTracker:
    """
    Realtime Observability & FinOps Dashboard com Depurador Rich no Terminal.
    Monitora métricas de processamento, limites de API, custos FinOps e logs de diagnóstico.
    """
    def __init__(self, total_tasks: int):
        self.stats = TelemetryStats(total_tasks=total_tasks)
        self.console = Console(force_terminal=True)
        self.finops_engine = FinOpsEngine()
        self._lock = asyncio.Lock()

    async def record_success(
        self,
        input_tokens: int,
        output_tokens: int,
        duration_sec: float,
        provider: str = "Groq",
        model: str = "groq/compound-mini"
    ):
        async with self._lock:
            self.stats.completed_tasks += 1
            self.stats.total_input_tokens += input_tokens
            self.stats.total_output_tokens += output_tokens

            # FinOps Realtime Calculation
            finops_res = self.finops_engine.calculate_cost(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                is_free_tier=True
            )
            self.stats.equivalent_cost_brl += finops_res.equivalent_cost_brl
            self.stats.savings_brl += finops_res.savings_brl

            event = f"[green]Sucesso[/green] [{provider}] {input_tokens}in/{output_tokens}out ({duration_sec:.2f}s) - Eq: R$ {finops_res.equivalent_cost_brl:.4f}"
            self._add_event(event)

    async def record_retry(self, attempt: int, reason: str, delay: float):
        async with self._lock:
            self.stats.retried_tasks += 1
            if "429" in reason:
                self.stats.count_429 += 1
            event = f"[yellow]ALERTA - Retry #{attempt}[/yellow]: {reason} (pausa adaptativa {delay:.1f}s)"
            self._add_event(event)

    async def record_failure(self, task_id: str, error: str):
        async with self._lock:
            self.stats.failed_tasks += 1
            event = f"[bold red]ERRO CRÍTICO - Falha na Tarefa {task_id}[/bold red]: {error}"
            self._add_event(event)

    async def update_limits_state(
        self,
        rem_rpm: int,
        rem_tpm: int,
        rpm_reset: float,
        tpm_reset: float,
        active_workers: int,
        status: str = "Processando",
        provider_name: Optional[str] = None
    ):
        async with self._lock:
            self.stats.rem_rpm = rem_rpm
            self.stats.rem_tpm = rem_tpm
            self.stats.rpm_reset_sec = rpm_reset
            self.stats.tpm_reset_sec = tpm_reset
            self.stats.active_workers = active_workers
            self.stats.current_status = status

            if provider_name:
                self.stats.provider_snapshots[provider_name] = QuotaSnapshot(
                    rpm_remaining=rem_rpm,
                    tpm_remaining=rem_tpm,
                    rpd_remaining=1000,
                    tpd_remaining=1000000,
                    rpm_reset_in_sec=rpm_reset,
                    tpm_reset_in_sec=tpm_reset
                )

    def _add_event(self, event: str):
        self.stats.recent_events.append(f"[{time.strftime('%H:%M:%S')}] {event}")
        if len(self.stats.recent_events) > 8:
            self.stats.recent_events.pop(0)

    def create_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=10)
        )
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )
        return layout

    def build_header(self) -> Panel:
        s = self.stats
        elapsed = time.time() - s.start_time
        return Panel(
            f"[bold cyan]LLM Traffic Controller & Daycoval Auditor[/bold cyan] | "
            f"Tempo: [bold green]{elapsed:.1f}s[/bold green] | "
            f"Status: [bold yellow]{s.current_status}[/bold yellow]",
            style="bold white on blue"
        )

    def build_metrics_table(self) -> Table:
        s = self.stats
        table = Table(title="[bold]Metricas de Processamento & FinOps[/bold]", expand=True)
        table.add_column("Metrica", style="cyan", no_wrap=True)
        table.add_column("Valor", style="magenta")

        total_tokens = s.total_input_tokens + s.total_output_tokens
        elapsed = max(0.1, time.time() - s.start_time)
        tpm_rate = int((total_tokens / elapsed) * 60)
        rpm_rate = int((s.completed_tasks / elapsed) * 60)

        table.add_row("Progresso Lote", f"{s.completed_tasks}/{s.total_tasks} ({(s.completed_tasks/max(1, s.total_tasks))*100:.1f}%)")
        table.add_row("Workers Ativos", str(s.active_workers))
        table.add_row("Input Tokens", f"{s.total_input_tokens:,}")
        table.add_row("Output Tokens", f"{s.total_output_tokens:,}")
        table.add_row("Total de Tokens", f"{total_tokens:,}")
        table.add_row("Throughput TPM / RPM", f"{tpm_rate:,} t/m | {rpm_rate} r/m")
        table.add_row("Custo Real API (Free)", "[bold green]R$ 0,00[/bold green]")
        table.add_row("Custo Comercial Eq.", f"[bold yellow]R$ {s.equivalent_cost_brl:.2f}[/bold yellow]")
        table.add_row("Economia Estimada", f"[bold green]R$ {s.savings_brl:.2f}[/bold green]")
        table.add_row("Retries / 429 Errors", f"[yellow]{s.retried_tasks}[/yellow] / [red]{s.count_429}[/red]")
        return table

    def build_limits_panel(self) -> Panel:
        s = self.stats
        table = Table(title="[bold]Governador Multi-Provedor (Limites API)[/bold]", expand=True)
        
        if s.provider_snapshots:
            table.add_column("Provedor", style="cyan")
            table.add_column("Saldo TPM", style="bold green")
            table.add_column("Saldo RPM", style="bold green")
            table.add_column("Reset TPM", style="bold yellow")

            for name, snap in s.provider_snapshots.items():
                table.add_row(
                    name,
                    f"{snap.tpm_remaining:,} tok",
                    f"{snap.rpm_remaining} reqs",
                    f"{snap.tpm_reset_in_sec:.1f}s"
                )
        else:
            table.add_column("Recurso", style="cyan")
            table.add_column("Saldo Restante", style="bold green")
            table.add_column("Reset", style="bold yellow")

            table.add_row("Requests (RPM)", f"{s.rem_rpm} reqs", f"{s.rpm_reset_sec:.1f}s")
            table.add_row("Tokens (TPM)", f"{s.rem_tpm:,} tokens", f"{s.tpm_reset_sec:.1f}s")

        return Panel(table, title="[bold]Quota Headroom Pool[/bold]")

    def build_events_panel(self) -> Panel:
        s = self.stats
        events_str = "\n".join(s.recent_events) if s.recent_events else "[dim]Nenhum evento crítico até o momento. Depurador ativo.[/dim]"
        return Panel(
            events_str,
            title="[bold red]Depurador Rich de Logs & Diagnóstico em Tempo Real[/bold red]",
            border_style="red" if s.failed_tasks > 0 else "yellow"
        )

    def render(self) -> Layout:
        layout = self.create_layout()
        layout["header"].update(self.build_header())
        layout["left"].update(self.build_metrics_table())
        layout["right"].update(self.build_limits_panel())
        layout["footer"].update(self.build_events_panel())
        return layout
