import os
import glob
import sys
import time
import asyncio
import argparse
import random
import threading
from typing import List, Dict

# Ensure UTF-8 output encoding for Windows terminal compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import uvicorn
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel

from rate_limiter import QuotaLimits, DynamicRateLimiter, MultiProviderRateLimiter
from concurrency_manager import ConcurrencyManager
from retry_manager import RetryManager
from tokenizer import TokenizerManager
from provider_groq import GroqProvider
from provider_gemini import GeminiProvider
from provider_openrouter import OpenRouterMiniMaxProvider
from queue_manager import BatchQueueProcessor
from telemetry import TelemetryTracker
from key_loader import KeyLoader
from database import AuditDatabase
from web_dashboard import app as web_app

console = Console(force_terminal=True)

def load_real_transcriptions(transcricoes_dir: str = r"C:\Users\fferr\Desktop\projetoRATE\transcricoes", limit: int = None) -> List[Dict[str, str]]:
    """Loads real transcription TXT files from transcricoes/ directory."""
    files = glob.glob(os.path.join(transcricoes_dir, "*.txt"))
    if not files:
        logger.warning(f"No transcription files found in {transcricoes_dir}. Generating synthetic fallback tasks.")
        return []

    if limit and limit > 0:
        files = files[:limit]

    tasks = []
    for fpath in files:
        fname = os.path.basename(fpath)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read().strip()
                if text:
                    tasks.append({
                        "id": fname,
                        "filename": fname,
                        "text": text
                    })
        except Exception as e:
            console.print(f"[yellow]Could not read {fname}: {e}[/yellow]")
    return tasks

import socket

def find_available_port(start_port: int = 8000) -> int:
    for port in range(start_port, start_port + 50):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return start_port

def start_web_dashboard_server(port: int = 8000) -> int:
    """Starts FastAPI uvicorn Web Dashboard in a background thread on an available port."""
    actual_port = find_available_port(port)
    def _run():
        try:
            uvicorn.run(web_app, host="127.0.0.1", port=actual_port, log_level="warning")
        except Exception as e:
            console.print(f"[yellow]Web server warning: {e}[/yellow]")
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    console.print(f"[bold green]Web Dashboard rodando em: http://127.0.0.1:{actual_port}[/bold green]")
    return actual_port

async def run_system(
    provider_type: str = "multi_real",
    num_transcriptions: int = None,
    rpm_limit: int = 30,
    tpm_limit: int = 8000,
    max_concurrency: int = 15,
    api_key: str = None,
    start_web: bool = True,
    web_port: int = 8000
):
    if start_web:
        web_port = start_web_dashboard_server(port=web_port)

    loaded_keys = KeyLoader().load_keys()

    # Load real transcriptions
    raw_tasks = load_real_transcriptions(limit=num_transcriptions)
    if not raw_tasks:
        console.print("[yellow]Nenhuma transcrição real encontrada em transcricoes/. Gerando tarefas de teste.[/yellow]")
        raw_tasks = [{"id": f"test_{i+1:03d}.txt", "filename": f"test_{i+1:03d}.txt", "text": "Cliente telefona para solicitar saldo e o operador realiza a autenticação."} for i in range(10)]

    console.print(Panel.fit(
        f"[bold blue]LLM API Traffic Controller & Daycoval Auditor[/bold blue]\n"
        f"Modo: [yellow]{provider_type.upper()}[/yellow] | Transcrições Reais: [cyan]{len(raw_tasks)}[/cyan]\n"
        f"Chaves -> Groq: [green]{'OK' if loaded_keys.groq_api_key else 'Mock'}[/green] | "
        f"Gemini: [green]{'OK' if loaded_keys.gemini_api_key else 'Mock'}[/green] | "
        f"MiniMax: [green]{'OK' if loaded_keys.openrouter_api_key else 'Mock'}[/green]\n"
        f"Web Dashboard: [bold underline green]http://127.0.0.1:{web_port}[/bold underline green]",
        title="[bold green]Inicializando Sistema de Auditoria[/bold green]"
    ))

    tokenizer = TokenizerManager()
    concurrency_mgr = ConcurrencyManager(max_concurrency=max_concurrency)
    db = AuditDatabase()

    providers = []
    limiters_map = {}

    if provider_type in ["multi_real", "multi_mock"]:
        is_mock = (provider_type == "multi_mock")
        
        # 1. Groq Provider
        groq_k = api_key or loaded_keys.groq_api_key
        p_groq = GroqProvider(api_key=groq_k, mock_mode=is_mock or not groq_k)
        l_groq = DynamicRateLimiter(QuotaLimits(rpm=30, tpm=14400), provider_name=p_groq.name, safe_tpm_percentage=0.80)
        providers.append(p_groq)
        limiters_map[p_groq.name] = l_groq

        # 2. Gemini Provider (gemini-3.6-flash) - Gemini Free Tier limit: 15 RPM
        gemini_k = loaded_keys.gemini_api_key
        p_gemini = GeminiProvider(api_key=gemini_k, mock_mode=is_mock or not gemini_k)
        l_gemini = DynamicRateLimiter(QuotaLimits(rpm=15, tpm=1000000), provider_name=p_gemini.name, safe_tpm_percentage=0.80)
        providers.append(p_gemini)
        limiters_map[p_gemini.name] = l_gemini

        # 3. MiniMax M3 Provider (via OpenRouter)
        openrouter_k = loaded_keys.openrouter_api_key
        p_minimax = OpenRouterMiniMaxProvider(api_key=openrouter_k, mock_mode=is_mock or not openrouter_k)
        l_minimax = DynamicRateLimiter(QuotaLimits(rpm=20, tpm=200000), provider_name=p_minimax.name, safe_tpm_percentage=0.80)
        providers.append(p_minimax)
        limiters_map[p_minimax.name] = l_minimax

        rate_limiter = MultiProviderRateLimiter(limiters_map)
        retry_mgr = RetryManager(max_retries=5, base_delay=2.0)
    else:
        if provider_type == "groq_real":
            p = GroqProvider(api_key=api_key or loaded_keys.groq_api_key, mock_mode=False)
        elif provider_type == "gemini_real":
            p = GeminiProvider(api_key=loaded_keys.gemini_api_key, mock_mode=False)
        elif provider_type == "minimax_real":
            p = OpenRouterMiniMaxProvider(api_key=loaded_keys.openrouter_api_key, mock_mode=False)
        elif provider_type == "gemini_mock":
            p = GeminiProvider(mock_mode=True)
        elif provider_type == "minimax_mock":
            p = OpenRouterMiniMaxProvider(mock_mode=True)
        else:
            p = GroqProvider(mock_mode=True)

        providers = [p]
        single_limiter = DynamicRateLimiter(QuotaLimits(rpm=rpm_limit, tpm=tpm_limit), provider_name=p.name)
        rate_limiter = MultiProviderRateLimiter({p.name: single_limiter})
        retry_mgr = RetryManager(max_retries=5, base_delay=1.0, rate_limiter=single_limiter)

    telemetry = TelemetryTracker(total_tasks=len(raw_tasks))

    processor = BatchQueueProcessor(
        provider=providers,
        rate_limiter=rate_limiter,
        concurrency_manager=concurrency_mgr,
        retry_manager=retry_mgr,
        telemetry=telemetry,
        database=db,
        tokenizer=tokenizer
    )

    processor.add_transcriptions(raw_tasks)

    start_time = time.time()
    
    async def dashboard_updater(live: Live):
        while True:
            for p in providers:
                lim = rate_limiter.get_limiter(p.name)
                if lim:
                    snap = lim.get_snapshot()
                    await telemetry.update_limits_state(
                        rem_rpm=snap.rpm_remaining,
                        rem_tpm=snap.tpm_remaining,
                        rpm_reset=snap.rpm_reset_in_sec,
                        tpm_reset=snap.tpm_reset_in_sec,
                        active_workers=concurrency_mgr.active_count,
                        status="Auditando Transcrições Reais",
                        provider_name=p.name
                    )
            live.update(telemetry.render())
            await asyncio.sleep(0.1)

    with Live(telemetry.render(), refresh_per_second=10, console=console) as live:
        updater_task = asyncio.create_task(dashboard_updater(live))
        try:
            await processor.run(num_workers=max_concurrency)
        finally:
            updater_task.cancel()

    elapsed = time.time() - start_time

    s = telemetry.stats
    total_tokens = s.total_input_tokens + s.total_output_tokens
    
    summary_table = Table(title="Relatorio Final de Execucao (Auditoria Daycoval & LLM Traffic Controller)", expand=True)
    summary_table.add_column("Metrica", style="cyan")
    summary_table.add_column("Resultado", style="bold green")

    summary_table.add_row("Tempo Total de Execucao", f"{elapsed:.2f} segundos")
    summary_table.add_row("Transcrições Reais Auditadas", f"{s.completed_tasks} / {len(raw_tasks)}")
    summary_table.add_row("Total de Tokens Processados", f"{total_tokens:,}")
    summary_table.add_row("Throughput Medio (TPM)", f"{int((total_tokens / max(0.1, elapsed))*60):,} tokens/min")
    summary_table.add_row("Throughput Medio (RPM)", f"{int((s.completed_tasks / max(0.1, elapsed))*60)} reqs/min")
    summary_table.add_row("Retries / HTTP 429 Bloqueios", f"{s.retried_tasks} / {s.count_429}")
    summary_table.add_row("Banco de Dados SQLite", f"repositoy/audit_database.db ({s.completed_tasks} registros)")
    summary_table.add_row("SaaS Admin Web Dashboard", f"http://127.0.0.1:{web_port}")

    console.print("\n")
    console.print(summary_table)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM Traffic Controller & Call Quality Auditor")
    parser.add_argument("--provider", choices=["multi_real", "multi_mock", "groq_real", "groq_mock", "gemini_real", "gemini_mock", "minimax_real", "minimax_mock"], default="multi_real", help="Provedor ou modo de execucao")
    parser.add_argument("--tasks", type=int, default=None, help="Limite de transcricoes reais a processar (default: todas as 309)")
    parser.add_argument("--rpm", type=int, default=30, help="Limite de RPM")
    parser.add_argument("--tpm", type=int, default=8000, help="Limite de TPM")
    parser.add_argument("--concurrency", type=int, default=15, help="Concorrencia maxima de workers")
    parser.add_argument("--api-key", type=str, default=None, help="Chave de API customizada (opcional)")
    parser.add_argument("--port", type=int, default=8080, help="Porta do Web Dashboard")

    args = parser.parse_args()

    try:
        asyncio.run(run_system(
            provider_type=args.provider,
            num_transcriptions=args.tasks,
            rpm_limit=args.rpm,
            tpm_limit=args.tpm,
            max_concurrency=args.concurrency,
            api_key=args.api_key,
            web_port=args.port
        ))
    except KeyboardInterrupt:
        console.print("\n[bold red]Execucao interrompida pelo usuario.[/bold red]")
