import os
import json
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from database import AuditDatabase
from finops_engine import FinOpsEngine

logger = logging.getLogger("TrafficController.WebDashboard")

app = FastAPI(title="LLM API Traffic Controller - SaaS Admin Dashboard & FinOps")
db = AuditDatabase()
finops_engine = FinOpsEngine()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Traffic Controller & FinOps Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: {
                            50: '#eff6ff',
                            500: '#3b82f6',
                            600: '#2563eb',
                            900: '#1e3a8a',
                        },
                        darkbg: '#0f172a',
                        cardbg: '#1e293b'
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-darkbg text-slate-100 min-h-screen font-sans antialiased">
    <!-- Top Navigation Header -->
    <header class="bg-cardbg border-b border-slate-700/60 px-6 py-4 flex justify-between items-center sticky top-0 z-50 shadow-md">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-lg">
                TC
            </div>
            <div>
                <h1 class="text-lg font-bold text-white tracking-wide">LLM Traffic Controller & Auditoria Daycoval</h1>
                <p class="text-xs text-slate-400">Governador Multi-Provedor • Painel Executivo FinOps IA</p>
            </div>
        </div>
        <div class="flex items-center space-x-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span class="w-2 h-2 rounded-full bg-emerald-400 mr-2 animate-pulse"></span>
                Governador & FinOps Ativo
            </span>
            <button onclick="refreshData()" class="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium rounded-lg transition shadow-md flex items-center space-x-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                <span>Atualizar</span>
            </button>
        </div>
    </header>

    <main class="p-6 max-w-7xl mx-auto space-y-6">
        <!-- Executive KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div class="bg-cardbg rounded-2xl p-5 border border-slate-700/60 shadow-lg">
                <div class="flex items-center justify-between text-slate-400 mb-2">
                    <span class="text-xs font-semibold uppercase tracking-wider">Atendimentos Auditados</span>
                    <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                </div>
                <div class="text-3xl font-extrabold text-white" id="kpi-audits">0</div>
                <div class="text-xs text-slate-400 mt-2">Transcrições salvas no SQLite</div>
            </div>

            <div class="bg-cardbg rounded-2xl p-5 border border-slate-700/60 shadow-lg">
                <div class="flex items-center justify-between text-slate-400 mb-2">
                    <span class="text-xs font-semibold uppercase tracking-wider">Média de Qualidade</span>
                    <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path></svg>
                </div>
                <div class="text-3xl font-extrabold text-white" id="kpi-score">0.0</div>
                <div class="text-xs text-emerald-400 mt-2">Score Global (0-100)</div>
            </div>

            <div class="bg-cardbg rounded-2xl p-5 border border-slate-700/60 shadow-lg">
                <div class="flex items-center justify-between text-slate-400 mb-2">
                    <span class="text-xs font-semibold uppercase tracking-wider">Riscos Críticos</span>
                    <svg class="w-5 h-5 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                </div>
                <div class="text-3xl font-extrabold text-rose-400" id="kpi-risks">0</div>
                <div class="text-xs text-slate-400 mt-2">Alertas de complacência</div>
            </div>

            <div class="bg-cardbg rounded-2xl p-5 border border-slate-700/60 shadow-lg">
                <div class="flex items-center justify-between text-slate-400 mb-2">
                    <span class="text-xs font-semibold uppercase tracking-wider">Total Tokens LLM</span>
                    <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                </div>
                <div class="text-3xl font-extrabold text-white" id="kpi-tokens">0</div>
                <div class="text-xs text-purple-300 mt-2" id="kpi-tokens-breakdown">In: 0 | Out: 0</div>
            </div>
        </div>

        <!-- FinOps Executive Cards with MANDATORY TOOLTIPS -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div class="bg-cardbg rounded-2xl p-5 border border-slate-700/60 shadow-lg">
                <div class="flex items-center justify-between text-slate-400 mb-2">
                    <span class="text-xs font-semibold uppercase tracking-wider">Custo Real API</span>
                    <span class="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">Free Tier</span>
                </div>
                <div class="text-3xl font-extrabold text-emerald-400" id="finops-actual">R$ 0,00</div>
                <div class="text-xs text-slate-400 mt-2">Valor desembolsado</div>
            </div>

            <div class="bg-cardbg rounded-2xl p-5 border border-slate-700/60 shadow-lg relative group">
                <div class="flex items-center justify-between text-slate-400 mb-2">
                    <span class="text-xs font-semibold uppercase tracking-wider">Custo Equivalente</span>
                    <svg class="w-4 h-4 text-amber-400 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                </div>
                <div class="text-3xl font-extrabold text-amber-400" id="finops-equivalent">R$ 0,00</div>
                <div class="text-xs text-slate-400 mt-2">Tabela comercial comercial pago</div>
                <!-- MANDATORY TOOLTIP -->
                <div class="absolute bottom-full left-0 mb-2 w-72 p-3 bg-slate-900 text-xs text-slate-200 rounded-xl shadow-2xl border border-slate-700 hidden group-hover:block z-50">
                    O custo equivalente representa quanto o mesmo consumo de tokens custaria utilizando a tabela comercial vigente do respectivo modelo. Não representa cobrança efetivamente realizada.
                </div>
            </div>

            <div class="bg-cardbg rounded-2xl p-5 border border-slate-700/60 shadow-lg relative group">
                <div class="flex items-center justify-between text-slate-400 mb-2">
                    <span class="text-xs font-semibold uppercase tracking-wider">Economia Estimada</span>
                    <svg class="w-4 h-4 text-emerald-400 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                </div>
                <div class="text-3xl font-extrabold text-emerald-400" id="finops-savings">R$ 0,00</div>
                <div class="text-xs text-emerald-400 mt-2">Free Tier vs. Comercial Pago</div>
                <!-- MANDATORY TOOLTIP -->
                <div class="absolute bottom-full left-0 mb-2 w-72 p-3 bg-slate-900 text-xs text-slate-200 rounded-xl shadow-2xl border border-slate-700 hidden group-hover:block z-50">
                    Diferença entre o custo comercial equivalente e o valor efetivamente pago pela solução.
                </div>
            </div>

            <div class="bg-cardbg rounded-2xl p-5 border border-slate-700/60 shadow-lg">
                <div class="flex items-center justify-between text-slate-400 mb-2">
                    <span class="text-xs font-semibold uppercase tracking-wider">Custo / Atendimento</span>
                    <svg class="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>
                </div>
                <div class="text-3xl font-extrabold text-indigo-400" id="finops-cost-per-call">R$ 0,00</div>
                <div class="text-xs text-slate-400 mt-2">Média ponderada por chamada</div>
            </div>
        </div>

        <!-- FinOps Capacity Planning & Projeções Mensais -->
        <div class="bg-cardbg rounded-2xl p-6 border border-slate-700/60 shadow-lg">
            <h3 class="text-base font-bold text-white mb-4 flex items-center space-x-2">
                <svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z"></path></svg>
                <span>FINOPS IA — Capacity Planning & Projeções Financeiras Mensais</span>
            </h3>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm text-slate-300">
                    <thead class="bg-slate-800/80 text-xs uppercase tracking-wider text-slate-400">
                        <tr>
                            <th class="px-6 py-3">Escala Mensal</th>
                            <th class="px-6 py-3">Tokens Entrada Otimizados</th>
                            <th class="px-6 py-3">Tokens Saída (Respostas)</th>
                            <th class="px-6 py-3">Tokens Totais Projetados</th>
                            <th class="px-6 py-3">Custo Eq. Mensal (USD)</th>
                            <th class="px-6 py-3">Custo Eq. Mensal (BRL)</th>
                        </tr>
                    </thead>
                    <tbody id="projection-table-body" class="divide-y divide-slate-700/50 font-mono text-xs">
                        <tr><td colspan="6" class="text-center py-4 text-slate-500">Calculando projeções baseadas no volume real...</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="mt-4 text-xs text-slate-400 flex justify-between items-center">
                <span>* Cotação aplicada: <strong class="text-amber-300">USD 1,00 = BRL 5,1262</strong> (Fonte: Banco Central / Comercial 05/09/2026)</span>
                <span class="px-3 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full font-bold">Identificado como SIMULAÇÃO PROJETADA</span>
            </div>
        </div>

        <!-- Charts Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-cardbg rounded-2xl p-5 border border-slate-700/60 shadow-lg">
                <h3 class="text-sm font-bold text-white mb-4 flex items-center space-x-2">
                    <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"></path></svg>
                    <span>Distribuição de Nível de Risco</span>
                </h3>
                <div class="h-64 flex justify-center items-center">
                    <canvas id="riskChart"></canvas>
                </div>
            </div>

            <div class="bg-cardbg rounded-2xl p-5 border border-slate-700/60 shadow-lg">
                <h3 class="text-sm font-bold text-white mb-4 flex items-center space-x-2">
                    <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z"></path></svg>
                    <span>Throughput por Provedor LLM</span>
                </h3>
                <div class="h-64 flex justify-center items-center">
                    <canvas id="providerChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Table Audit Section -->
        <div class="bg-cardbg rounded-2xl border border-slate-700/60 shadow-lg overflow-hidden">
            <div class="p-5 border-b border-slate-700/60 flex flex-col md:flex-row justify-between md:items-center space-y-3 md:space-y-0">
                <h3 class="text-base font-bold text-white flex items-center space-x-2">
                    <svg class="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path></svg>
                    <span>Auditorias Recentes de Atendimento</span>
                </h3>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm text-slate-300">
                    <thead class="bg-slate-800/80 text-xs uppercase tracking-wider text-slate-400">
                        <tr>
                            <th class="px-6 py-3">Arquivo</th>
                            <th class="px-6 py-3">Protocolo</th>
                            <th class="px-6 py-3">Operador</th>
                            <th class="px-6 py-3">Score Final</th>
                            <th class="px-6 py-3">Nível de Risco</th>
                            <th class="px-6 py-3">Provedor LLM</th>
                            <th class="px-6 py-3">Ações</th>
                        </tr>
                    </thead>
                    <tbody id="audit-table-body" class="divide-y divide-slate-700/50">
                        <tr>
                            <td colspan="7" class="text-center py-8 text-slate-500">Carregando dados do banco de dados...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <!-- Modal for Detailed Audit View -->
    <div id="auditModal" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
        <div class="bg-cardbg border border-slate-700 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 relative">
            <button onclick="closeModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
            <div id="modalContent"></div>
        </div>
    </div>

    <script>
        let riskChart, providerChart;

        async function fetchKPIs() {
            const res = await fetch('/api/kpis');
            const data = await res.json();
            document.getElementById('kpi-audits').innerText = data.total_audits;
            document.getElementById('kpi-score').innerText = data.avg_score;
            document.getElementById('kpi-risks').innerText = data.high_risks;
            document.getElementById('kpi-tokens').innerText = data.total_tokens.toLocaleString();
        }

        async function fetchFinOps() {
            const res = await fetch('/api/finops');
            const data = await res.json();
            const summary = data.summary;
            const proj = data.projections;

            document.getElementById('kpi-tokens-breakdown').innerText = `In: ${summary.total_input_tokens.toLocaleString()} | Out: ${summary.total_output_tokens.toLocaleString()}`;
            document.getElementById('finops-actual').innerText = `R$ ${summary.actual_cost_brl.toFixed(2)}`;
            document.getElementById('finops-equivalent').innerText = `R$ ${summary.equivalent_cost_brl.toFixed(2)}`;
            document.getElementById('finops-savings').innerText = `R$ ${summary.savings_brl.toFixed(2)}`;
            document.getElementById('finops-cost-per-call').innerText = `R$ ${summary.cost_per_call_brl.toFixed(4)}`;

            // Render Projection Table
            const tbody = document.getElementById('projection-table-body');
            tbody.innerHTML = '';
            
            Object.values(proj).forEach(p => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/40 transition";
                tr.innerHTML = `
                    <td class="px-6 py-3 font-bold text-white">${p.monthly_calls.toLocaleString()} chamadas/mês</td>
                    <td class="px-6 py-3">${p.projected_input_tokens.toLocaleString()}</td>
                    <td class="px-6 py-3">${p.projected_output_tokens.toLocaleString()}</td>
                    <td class="px-6 py-3 font-bold text-purple-300">${p.projected_total_tokens.toLocaleString()}</td>
                    <td class="px-6 py-3 text-amber-300">US$ ${p.equivalent_cost_usd.toLocaleString()}</td>
                    <td class="px-6 py-3 font-bold text-emerald-400">R$ ${p.equivalent_cost_brl.toLocaleString()}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function fetchAudits() {
            const res = await fetch('/api/audits');
            const audits = await res.json();
            const tbody = document.getElementById('audit-table-body');
            tbody.innerHTML = '';

            if (audits.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-slate-500">Nenhum atendimento auditado ainda. Execute main.py para iniciar.</td></tr>';
                return;
            }

            let riskCounts = { Baixo: 0, Médio: 0, Alto: 0, Crítico: 0 };
            let providerCounts = {};

            audits.forEach(a => {
                const risk = a.risk_level || 'Baixo';
                riskCounts[risk] = (riskCounts[risk] || 0) + 1;
                const prov = a.provider_used || 'Groq';
                providerCounts[prov] = (providerCounts[prov] || 0) + 1;

                let scoreBadge = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
                if (a.overall_score < 70) scoreBadge = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
                else if (a.overall_score < 85) scoreBadge = 'bg-amber-500/10 text-amber-400 border-amber-500/20';

                let riskBadge = 'bg-slate-700 text-slate-300';
                if (risk === 'Alto' || risk === 'Crítico') riskBadge = 'bg-rose-600 text-white font-bold';

                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/40 transition";
                tr.innerHTML = `
                    <td class="px-6 py-4 font-mono text-xs text-blue-300">${a.filename}</td>
                    <td class="px-6 py-4">${a.protocol_number || 'N/A'}</td>
                    <td class="px-6 py-4">${a.operator_name || 'Operador'}</td>
                    <td class="px-6 py-4"><span class="px-3 py-1 rounded-full text-xs border ${scoreBadge}">${a.overall_score}</span></td>
                    <td class="px-6 py-4"><span class="px-2.5 py-0.5 rounded text-xs ${riskBadge}">${risk}</span></td>
                    <td class="px-6 py-4"><span class="text-xs px-2 py-1 rounded bg-slate-800 text-purple-300 border border-purple-500/30">${a.provider_used || 'Groq'}</span></td>
                    <td class="px-6 py-4">
                        <button onclick='openModal(${JSON.stringify(a).replace(/'/g, "&apos;")})' class="text-xs bg-slate-700 hover:bg-slate-600 text-white px-3 py-1.5 rounded transition">
                            Detalhes
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

            renderCharts(riskCounts, providerCounts);
        }

        function renderCharts(riskCounts, providerCounts) {
            if (riskChart) riskChart.destroy();
            if (providerChart) providerChart.destroy();

            const ctx1 = document.getElementById('riskChart').getContext('2d');
            riskChart = new Chart(ctx1, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(riskCounts),
                    datasets: [{
                        data: Object.values(riskCounts),
                        backgroundColor: ['#10b981', '#f59e0b', '#f97316', '#ef4444']
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#cbd5e1' } } } }
            });

            const ctx2 = document.getElementById('providerChart').getContext('2d');
            providerChart = new Chart(ctx2, {
                type: 'bar',
                data: {
                    labels: Object.keys(providerCounts),
                    datasets: [{
                        label: 'Requisições Atendidas',
                        data: Object.values(providerCounts),
                        backgroundColor: '#3b82f6'
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#cbd5e1' } } }, scales: { y: { ticks: { color: '#cbd5e1' } }, x: { ticks: { color: '#cbd5e1' } } } }
            });
        }

        function openModal(audit) {
            const content = document.getElementById('modalContent');
            content.innerHTML = `
                <h2 class="text-xl font-bold text-white mb-2">Auditoria: ${audit.filename}</h2>
                <div class="text-xs text-slate-400 mb-4">Protocolo: ${audit.protocol_number} • Operador: ${audit.operator_name}</div>
                
                <div class="bg-slate-800/60 p-4 rounded-xl mb-4 border border-slate-700">
                    <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Resumo Executivo</h3>
                    <p class="text-sm text-slate-200">${audit.executive_summary}</p>
                </div>

                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="bg-slate-800/60 p-4 rounded-xl border border-slate-700">
                        <div class="text-xs text-slate-400">Score Final</div>
                        <div class="text-2xl font-bold text-emerald-400">${audit.overall_score} / 100</div>
                    </div>
                    <div class="bg-slate-800/60 p-4 rounded-xl border border-slate-700">
                        <div class="text-xs text-slate-400">Nível de Risco & Causa Raiz</div>
                        <div class="text-sm font-bold text-rose-400">${audit.risk_level}</div>
                        <div class="text-xs text-slate-300 mt-1">${audit.root_cause}</div>
                    </div>
                </div>

                <div class="bg-slate-800/60 p-4 rounded-xl border border-slate-700 mb-4">
                    <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Citação / Evidência</h3>
                    <p class="text-xs italic text-slate-300">"${audit.evidence_quote || 'Sem citação'}"</p>
                </div>
            `;
            document.getElementById('auditModal').classList.remove('hidden');
        }

        function closeModal() {
            document.getElementById('auditModal').classList.add('hidden');
        }

        function refreshData() {
            fetchKPIs();
            fetchFinOps();
            fetchAudits();
        }

        refreshData();
        setInterval(refreshData, 5000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    return HTML_TEMPLATE

@app.get("/api/kpis")
def get_kpis():
    return db.get_kpi_summary()

@app.get("/api/finops")
def get_finops():
    summary = db.get_finops_summary()
    projections = finops_engine.calculate_capacity_projections(
        avg_input_tokens_per_call=summary.get("avg_input_per_call", 1800),
        avg_output_tokens_per_call=summary.get("avg_output_per_call", 300)
    )
    return {
        "summary": summary,
        "projections": projections
    }

@app.get("/api/audits")
def get_audits():
    return db.get_all_audits(limit=200)

@app.get("/api/audit/{audit_id}")
def get_single_audit(audit_id: int):
    audits = db.get_all_audits(limit=500)
    for a in audits:
        if a["id"] == audit_id:
            return a
    raise HTTPException(status_code=404, detail="Audit not found")
