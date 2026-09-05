import os
import json
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Response, Depends, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from database import AuditDatabase
from finops_engine import FinOpsEngine

logger = logging.getLogger("TrafficController.WebDashboard")

app = FastAPI(title="AuditAI - Banco Engineer AI SaaS Dashboard & LLM Traffic Controller")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = AuditDatabase()
finops_engine = FinOpsEngine()

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    session_id = request.cookies.get("auditai_session") or request.headers.get("X-Session-ID")
    if not session_id:
        return None
    return db.get_user_by_session(session_id)

HTML_PAGE = """<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pathway LMS • AuditAI | Banco Engineer AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400;1,600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['"Plus Jakarta Sans"', 'sans-serif']
                    },
                    colors: {
                        brand: {
                            500: '#6366f1',
                            600: '#4f46e5',
                            700: '#4338ca'
                        },
                        darkbg: '#090d16',
                        cardbg: '#111827',
                        sidebg: '#0d1322'
                    }
                }
            }
        }
    </script>
    <style>
        .gold-gradient-btn {
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        }
        .gold-gradient-btn:hover {
            background: linear-gradient(135deg, #818cf8 0%, #4338ca 100%);
        }
        .custom-scrollbar::-webkit-scrollbar {
            width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
            background: #0d1322;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: #1f2937;
            border-radius: 4px;
        }
    </style>
</head>
<body class="bg-darkbg text-slate-100 font-sans antialiased selection:bg-brand-500 selection:text-white min-h-screen">

    <!-- LOGIN CONTAINER -->
    <div id="loginView" class="min-h-screen flex items-center justify-center p-4 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-950/40 via-darkbg to-darkbg">
        <div class="w-full max-w-md">
            <div class="text-center mb-8">
                <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 mb-4 shadow-xl shadow-indigo-600/10">
                    <i class="fa-solid fa-graduation-cap text-3xl"></i>
                </div>
                <h1 class="text-3xl font-extrabold text-white tracking-tight">Pathway LMS</h1>
                <p class="text-xs text-indigo-400 font-semibold mt-1">AuditAI • Banco Engineer AI Quality & Compliance</p>
            </div>

            <div class="bg-cardbg border border-slate-800 rounded-3xl p-8 shadow-2xl space-y-6">
                <div>
                    <h3 class="text-xl font-bold text-white">Acesse o Portal</h3>
                    <p class="text-xs text-slate-400 mt-1">Insira suas credenciais para visualizar métricas e relatórios.</p>
                </div>

                <form id="loginForm" onsubmit="handleLogin(event); return false;" action="javascript:void(0);" class="space-y-4">
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1.5">Usuário ou E-mail</label>
                        <input type="text" id="loginUsername" required placeholder="admin ou usuario" class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500">
                    </div>

                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1.5">Senha</label>
                        <input type="password" id="loginPassword" required placeholder="••••••••" class="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500">
                    </div>

                    <div id="loginError" class="text-xs text-rose-400 font-semibold hidden bg-rose-500/10 p-2.5 rounded-lg border border-rose-500/20 text-center"></div>

                    <button type="button" onclick="handleLogin(event)" class="w-full py-3.5 font-bold text-white rounded-xl gold-gradient-btn transition shadow-lg flex items-center justify-center space-x-2 text-sm tracking-wide">
                        <span>Entrar na Plataforma</span>
                        <i class="fa-solid fa-arrow-right"></i>
                    </button>
                </form>

                <div class="relative flex py-2 items-center">
                    <div class="flex-grow border-t border-slate-800"></div>
                    <span class="flex-shrink mx-4 text-xs text-slate-500">Acesso Rápido 1-Clique</span>
                    <div class="flex-grow border-t border-slate-800"></div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <button type="button" onclick="quickFill('admin', 'admin1')" class="py-2.5 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-bold rounded-xl transition flex items-center justify-center gap-1.5">
                        <i class="fa-solid fa-user-shield"></i> Admin Demo
                    </button>
                    <button type="button" onclick="quickFill('usuario', 'usuario1')" class="py-2.5 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-blue-300 text-xs font-bold rounded-xl transition flex items-center justify-center gap-1.5">
                        <i class="fa-solid fa-user"></i> Usuário Demo
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- MAIN LMS SAAS LAYOUT (Rendered when Logged In) -->
    <div id="appView" class="hidden min-h-screen flex bg-darkbg">

        <!-- LEFT SIDEBAR MENU (Pathway LMS Behance Style - Images 2, 3, 4, 5) -->
        <aside class="w-64 bg-sidebg border-r border-slate-800 flex flex-col justify-between shrink-0 hidden md:flex sticky top-0 h-screen z-40">
            <div class="p-6 space-y-8">
                <!-- Brand Header -->
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-indigo-600/30">
                        <i class="fa-solid fa-shapes"></i>
                    </div>
                    <div>
                        <div class="font-extrabold text-white text-base tracking-tight">Pathway LMS</div>
                        <div class="text-[10px] font-semibold text-indigo-400">Banco Engineer AI</div>
                    </div>
                </div>

                <!-- Navigation Section -->
                <nav class="space-y-1 text-xs font-medium" id="sideNav">
                    <button id="navDashboard" onclick="switchView('dashboard')" class="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-white bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 transition">
                        <i class="fa-solid fa-house w-4 text-center"></i>
                        <span>Dashboard</span>
                    </button>

                    <button id="navOperators" onclick="switchView('operators')" class="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/60 transition">
                        <i class="fa-solid fa-id-badge w-4 text-center"></i>
                        <span>Operadores</span>
                    </button>

                    <button id="navAudits" onclick="switchView('audits')" class="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/60 transition">
                        <i class="fa-solid fa-file-contract w-4 text-center"></i>
                        <span>Auditorias & Chamadas</span>
                    </button>

                    <button id="navAssessments" onclick="switchView('assessments')" class="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/60 transition">
                        <i class="fa-solid fa-chart-pie w-4 text-center"></i>
                        <span>Avaliações & Analytics</span>
                    </button>

                    <button id="navInfra" onclick="switchView('infra')" class="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/60 transition hidden">
                        <i class="fa-solid fa-bolt w-4 text-center"></i>
                        <span>Infraestrutura & FinOps</span>
                    </button>

                    <button id="navAdminPerm" onclick="switchView('admin_perm')" class="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/60 transition hidden">
                        <i class="fa-solid fa-user-gear w-4 text-center"></i>
                        <span>Gestão de Acessos</span>
                    </button>
                </nav>
            </div>

            <!-- Bottom Profile & Logout -->
            <div class="p-4 border-t border-slate-800 bg-slate-900/40">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3 overflow-hidden">
                        <div class="w-9 h-9 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 flex items-center justify-center font-bold text-xs shrink-0">
                            <i class="fa-solid fa-user-astronaut"></i>
                        </div>
                        <div class="truncate text-xs">
                            <div id="userName" class="font-bold text-white truncate">Administrador</div>
                            <div id="userRoleBadge" class="text-[10px] text-indigo-400 uppercase font-semibold">ADMIN</div>
                        </div>
                    </div>
                    <button onclick="handleLogout()" class="text-slate-400 hover:text-rose-400 p-2 rounded-lg transition" title="Sair">
                        <i class="fa-solid fa-right-from-bracket text-sm"></i>
                    </button>
                </div>
            </div>
        </aside>

        <!-- RIGHT CONTENT WRAPPER -->
        <div class="flex-1 flex flex-col min-w-0 overflow-y-auto custom-scrollbar">

            <!-- Top Header Navbar -->
            <header class="bg-cardbg/80 backdrop-blur border-b border-slate-800 px-6 py-4 flex items-center justify-between sticky top-0 z-30">
                <div>
                    <h2 id="pageTitle" class="text-xl font-extrabold text-white">Dashboard Overview</h2>
                    <p id="pageSubTitle" class="text-xs text-slate-400 mt-0.5">Acompanhe métricas de qualidade, conformidade e gestão de riscos em tempo real.</p>
                </div>

                <div class="flex items-center space-x-4">
                    <!-- Search Bar -->
                    <div class="relative hidden sm:block w-64">
                        <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                            <i class="fa-solid fa-magnifying-glass text-xs"></i>
                        </span>
                        <input type="text" id="globalSearch" oninput="handleGlobalSearch()" placeholder="Buscar protocolo, operador..." class="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500">
                    </div>

                    <button onclick="refreshData()" class="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition" title="Atualizar Dados">
                        <i class="fa-solid fa-arrows-rotate text-sm"></i>
                    </button>
                </div>
            </header>

            <!-- CONTENT BODY VIEWS -->
            <main class="p-6 max-w-7xl mx-auto space-y-6 flex-grow w-full">

                <!-- VIEW 1: HOME DASHBOARD (Behance LMS Image 2 & 3) -->
                <div id="viewDashboard" class="space-y-6">
                    
                    <!-- 4 Key Metrics Cards -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        <div class="bg-cardbg rounded-2xl p-5 border border-slate-800 shadow-lg flex items-center justify-between">
                            <div>
                                <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Auditorias</p>
                                <h3 id="exec-audits" class="text-2xl font-extrabold text-white mt-1">309</h3>
                                <p class="text-[10px] text-emerald-400 mt-1"><i class="fa-solid fa-arrow-trend-up"></i> 100% Salvos em SQLite</p>
                            </div>
                            <div class="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center text-xl">
                                <i class="fa-solid fa-users"></i>
                            </div>
                        </div>

                        <div class="bg-cardbg rounded-2xl p-5 border border-slate-800 shadow-lg flex items-center justify-between">
                            <div>
                                <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Média Qualidade CX</p>
                                <h3 id="exec-score" class="text-2xl font-extrabold text-emerald-400 mt-1">85.4</h3>
                                <p class="text-[10px] text-slate-400 mt-1">Scorecard de 0 a 100</p>
                            </div>
                            <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center text-xl">
                                <i class="fa-solid fa-award"></i>
                            </div>
                        </div>

                        <div class="bg-cardbg rounded-2xl p-5 border border-slate-800 shadow-lg flex items-center justify-between">
                            <div>
                                <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tokens Processados</p>
                                <h3 id="infra-tokens" class="text-2xl font-extrabold text-purple-400 mt-1">4.2M</h3>
                                <p class="text-[10px] text-purple-300 mt-1">Compressores Python ativos</p>
                            </div>
                            <div class="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center text-xl">
                                <i class="fa-solid fa-microchip"></i>
                            </div>
                        </div>

                        <div class="bg-cardbg rounded-2xl p-5 border border-slate-800 shadow-lg flex items-center justify-between">
                            <div>
                                <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Casos de Risco Crítico</p>
                                <h3 id="exec-risks" class="text-2xl font-extrabold text-rose-400 mt-1">12</h3>
                                <p class="text-[10px] text-rose-300 mt-1">Necessitam Ação Imediata</p>
                            </div>
                            <div class="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center text-xl">
                                <i class="fa-solid fa-triangle-exclamation"></i>
                            </div>
                        </div>
                    </div>

                    <!-- Middle Two-Column Grid (Behance Image 2 & 3: Top Performance + Engagement Ring) -->
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <!-- Top Performance Table (2 cols) -->
                        <div class="lg:col-span-2 bg-cardbg rounded-2xl p-6 border border-slate-800 shadow-lg space-y-4">
                            <div class="flex items-center justify-between">
                                <h3 class="text-base font-bold text-white flex items-center gap-2">
                                    <i class="fa-solid fa-fire text-amber-400"></i> Destaques de Atendimentos Auditados
                                </h3>
                                <button onclick="switchView('audits')" class="text-xs text-indigo-400 hover:underline font-semibold">Ver Todos <i class="fa-solid fa-chevron-right text-[10px]"></i></button>
                            </div>

                            <div class="overflow-x-auto">
                                <table class="w-full text-left border-collapse text-xs">
                                    <thead>
                                        <tr class="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                                            <th class="pb-3 px-3">Protocolo</th>
                                            <th class="pb-3 px-3">Operador</th>
                                            <th class="pb-3 px-3">Score CX</th>
                                            <th class="pb-3 px-3">Risco</th>
                                            <th class="pb-3 px-3 text-right">Ação</th>
                                        </tr>
                                    </thead>
                                    <tbody id="home-audits-preview" class="divide-y divide-slate-800/60">
                                        <!-- Loaded dynamically -->
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <!-- Learner / CX Engagement Ring Chart (1 col - Image 2 Donut) -->
                        <div class="bg-cardbg rounded-2xl p-6 border border-slate-800 shadow-lg flex flex-col justify-between space-y-4">
                            <h3 class="text-base font-bold text-white flex items-center gap-2">
                                <i class="fa-solid fa-chart-donut text-indigo-400"></i> Distribuição de Qualidade CX
                            </h3>
                            <div class="relative flex items-center justify-center h-48">
                                <canvas id="cxDonutChart"></canvas>
                            </div>
                            <div class="space-y-2 text-xs border-t border-slate-800 pt-4">
                                <div class="flex justify-between items-center"><span class="flex items-center gap-2 text-slate-300"><span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Conforme (>85)</span> <strong class="text-white font-mono" id="donut-high">0</strong></div>
                                <div class="flex justify-between items-center"><span class="flex items-center gap-2 text-slate-300"><span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Alerta (70-85)</span> <strong class="text-white font-mono" id="donut-med">0</strong></div>
                                <div class="flex justify-between items-center"><span class="flex items-center gap-2 text-slate-300"><span class="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Crítico (<70)</span> <strong class="text-white font-mono" id="donut-low">0</strong></div>
                            </div>
                        </div>
                    </div>

                    <!-- Bottom Alerts & Recent Activity -->
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div class="bg-cardbg rounded-2xl p-6 border border-slate-800 shadow-lg space-y-4">
                            <h3 class="text-base font-bold text-white flex items-center gap-2">
                                <i class="fa-solid fa-bell text-rose-400"></i> Alertas Importantes de Conformidade
                            </h3>
                            <div id="home-alerts-list" class="space-y-3">
                                <!-- Loaded dynamically -->
                            </div>
                        </div>

                        <div class="bg-cardbg rounded-2xl p-6 border border-slate-800 shadow-lg space-y-4">
                            <h3 class="text-base font-bold text-white flex items-center gap-2">
                                <i class="fa-solid fa-clock-rotate-left text-blue-400"></i> Atividades Recentes da Operação
                            </h3>
                            <div id="home-activity-list" class="space-y-3">
                                <!-- Loaded dynamically -->
                            </div>
                        </div>
                    </div>
                </div>

                <!-- VIEW 2: OPERATORES (Behance LMS Image 4 - Instructors List) -->
                <div id="viewOperators" class="space-y-6 hidden">
                    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-cardbg p-6 rounded-2xl border border-slate-800">
                        <div>
                            <h3 class="text-lg font-bold text-white">Desempenho da Equipe de Operadores</h3>
                            <p class="text-xs text-slate-400 mt-1">Ranking de atendentes baseado na nota média CX e resolutividade de chamadas.</p>
                        </div>
                        <div class="flex items-center gap-3">
                            <input type="text" id="opSearch" oninput="filterOperatorsTable()" placeholder="Buscar operador..." class="px-3.5 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500">
                        </div>
                    </div>

                    <div class="bg-cardbg rounded-2xl border border-slate-800 overflow-hidden shadow-lg">
                        <table class="w-full text-left border-collapse text-xs">
                            <thead>
                                <tr class="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                                    <th class="py-4 px-6">Operador</th>
                                    <th class="py-4 px-6">Atendimentos Auditados</th>
                                    <th class="py-4 px-6">Score Médio CX</th>
                                    <th class="py-4 px-6">Casos de Risco</th>
                                    <th class="py-4 px-6">Status de Desempenho</th>
                                    <th class="py-4 px-6 text-right">Ação</th>
                                </tr>
                            </thead>
                            <tbody id="operatorsTableBody" class="divide-y divide-slate-800/60">
                                <!-- Loaded dynamically -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- VIEW 3: AUDITORIAS & CHAMADAS (Behance LMS Image 2 & 4) -->
                <div id="viewAudits" class="space-y-6 hidden">
                    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-cardbg p-6 rounded-2xl border border-slate-800">
                        <div>
                            <h3 class="text-lg font-bold text-white">Todas as Auditorias de Atendimento</h3>
                            <p class="text-xs text-slate-400 mt-1">Consulte a íntegra dos 309 atendimentos com análise de causas raízes e transcrições.</p>
                        </div>

                        <div class="flex items-center gap-3 w-full md:w-auto">
                            <input type="text" id="execSearch" oninput="filterExecTable()" placeholder="Buscar protocolo, operador, arquivo..." class="px-3.5 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 w-full md:w-64">
                            <select id="execFilterRisk" onchange="filterExecTable()" class="px-3.5 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500">
                                <option value="ALL">Todos os Riscos</option>
                                <option value="Baixo">Baixo Risco</option>
                                <option value="Médio">Médio Risco</option>
                                <option value="Alto">Alto Risco</option>
                                <option value="Crítico">Crítico</option>
                            </select>
                        </div>
                    </div>

                    <div class="bg-cardbg rounded-2xl border border-slate-800 overflow-hidden shadow-lg">
                        <table class="w-full text-left border-collapse text-xs">
                            <thead>
                                <tr class="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                                    <th class="py-4 px-6">Protocolo / Arquivo</th>
                                    <th class="py-4 px-6">Operador</th>
                                    <th class="py-4 px-6">Cliente</th>
                                    <th class="py-4 px-6">Score Geral</th>
                                    <th class="py-4 px-6">Nível Risco</th>
                                    <th class="py-4 px-6">Provedor LLM</th>
                                    <th class="py-4 px-6 text-right">Inspeção</th>
                                </tr>
                            </thead>
                            <tbody id="exec-table-body" class="divide-y divide-slate-800/60">
                                <!-- Loaded dynamically -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- VIEW 4: AVALIAÇÕES & ANALYTICS (Behance LMS Image 5 - Assessments) -->
                <div id="viewAssessments" class="space-y-6 hidden">
                    <div class="bg-cardbg p-6 rounded-2xl border border-slate-800">
                        <h3 class="text-lg font-bold text-white">Análise Qualitativa CX & Dimensões Pydantic</h3>
                        <p class="text-xs text-slate-400 mt-1">Desempenho detalhado por pilar de atendimento e taxa de conformidade.</p>
                    </div>

                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div class="bg-cardbg p-6 rounded-2xl border border-slate-800 shadow-lg space-y-4">
                            <h4 class="text-sm font-bold text-white flex items-center gap-2">
                                <i class="fa-solid fa-chart-bar text-indigo-400"></i> Média por Dimensão Pydantic (0-100)
                            </h4>
                            <div class="h-64">
                                <canvas id="cxBarChart"></canvas>
                            </div>
                        </div>

                        <div class="bg-cardbg p-6 rounded-2xl border border-slate-800 shadow-lg space-y-4">
                            <h4 class="text-sm font-bold text-white flex items-center gap-2">
                                <i class="fa-solid fa-shield-halved text-emerald-400"></i> Distribuição Pass vs Fail (Riscos)
                            </h4>
                            <div class="h-64">
                                <canvas id="riskBarChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- VIEW 5: INFRAESTRUTURA & FINOPS (Dev/Admin Only) -->
                <div id="viewInfra" class="space-y-6 hidden">
                    <div class="bg-cardbg p-6 rounded-2xl border border-slate-800 space-y-2">
                        <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-purple-500/10 text-purple-400 text-xs font-bold border border-purple-500/20">
                            <span>Painel FinOps & Economia de LLM</span>
                        </div>
                        <h3 class="text-xl font-extrabold text-white">Gestão Financeira & Capacidade Operacional</h3>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div class="bg-cardbg p-6 rounded-2xl border border-slate-800 shadow-lg">
                            <div class="text-xs font-bold text-slate-400 uppercase">Custo Real Pago (Groq / Gemini)</div>
                            <div class="text-2xl font-extrabold text-emerald-400 mt-2" id="infra-actual">R$ 0.00</div>
                            <p class="text-[10px] text-slate-500 mt-1">Tier gratuito e modelos otimizados</p>
                        </div>
                        <div class="bg-cardbg p-6 rounded-2xl border border-slate-800 shadow-lg">
                            <div class="text-xs font-bold text-slate-400 uppercase">Custo Equivalente sem Otimizador</div>
                            <div class="text-2xl font-extrabold text-amber-400 mt-2" id="infra-equivalent">R$ 0.00</div>
                            <p class="text-[10px] text-slate-500 mt-1">Estimativa comercial padrão</p>
                        </div>
                        <div class="bg-cardbg p-6 rounded-2xl border border-slate-800 shadow-lg">
                            <div class="text-xs font-bold text-slate-400 uppercase">Economia Financeira Gerada</div>
                            <div class="text-2xl font-extrabold text-indigo-400 mt-2" id="infra-savings">R$ 0.00</div>
                            <p class="text-[10px] text-indigo-300 mt-1">Arquitetura Python First</p>
                        </div>
                    </div>

                    <div class="bg-cardbg p-6 rounded-2xl border border-slate-800 shadow-lg space-y-4">
                        <h4 class="text-sm font-bold text-white">Projeção de Capacidade & Escalabilidade</h4>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs">
                                <thead>
                                    <tr class="border-b border-slate-800 text-slate-400 font-semibold uppercase">
                                        <th class="py-3 px-4">Volume Mensal</th>
                                        <th class="py-3 px-4">Tokens Entrada</th>
                                        <th class="py-3 px-4">Tokens Saída</th>
                                        <th class="py-3 px-4">Total Tokens</th>
                                        <th class="py-3 px-4">Custo USD</th>
                                        <th class="py-3 px-4">Custo BRL</th>
                                    </tr>
                                </thead>
                                <tbody id="infra-proj-body" class="divide-y divide-slate-800/60"></tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- VIEW 6: GESTÃO DE ACESSOS (Admin Only) -->
                <div id="viewAdminPerm" class="space-y-6 hidden">
                    <div class="bg-cardbg p-6 rounded-2xl border border-slate-800">
                        <h3 class="text-lg font-bold text-white">Gestão de Permissões & Perfis de Usuário</h3>
                        <p class="text-xs text-slate-400 mt-1">Controle de visualizações para perfis Administrador e Usuário Padrão.</p>
                    </div>

                    <div class="bg-cardbg rounded-2xl border border-slate-800 overflow-hidden shadow-lg">
                        <table class="w-full text-left text-xs">
                            <thead>
                                <tr class="bg-slate-900 border-b border-slate-800 text-slate-400 font-semibold uppercase">
                                    <th class="py-4 px-6">Usuário</th>
                                    <th class="py-4 px-6">Perfil</th>
                                    <th class="py-4 px-6 text-center">Ver Infra / FinOps</th>
                                    <th class="py-4 px-6 text-center">Ver Dashboard Executivo</th>
                                    <th class="py-4 px-6 text-right">Ação</th>
                                </tr>
                            </thead>
                            <tbody id="permTableBody" class="divide-y divide-slate-800/60"></tbody>
                        </table>
                    </div>
                </div>

            </main>
        </div>
    </div>

    <!-- RIGHT SLIDE-OVER DRAWER (Behance LMS Image 4 - Learner Profile / Call Inspector) -->
    <div id="rightDrawerOverlay" onclick="closeRightDrawer()" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 hidden transition-opacity"></div>
    <aside id="rightDrawer" class="fixed top-0 right-0 w-full max-w-xl h-full bg-cardbg border-l border-slate-800 z-50 transform translate-x-full transition-transform duration-300 shadow-2xl flex flex-col justify-between overflow-hidden">
        <div class="p-6 border-b border-slate-800 flex items-center justify-between bg-sidebg">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center text-lg font-bold">
                    <i class="fa-solid fa-clipboard-check"></i>
                </div>
                <div>
                    <h3 id="drawerTitle" class="font-extrabold text-white text-base">Inspeção Detalhada</h3>
                    <p id="drawerSubTitle" class="text-xs text-slate-400">Relatório de Qualidade Pydantic</p>
                </div>
            </div>
            <button onclick="closeRightDrawer()" class="text-slate-400 hover:text-white p-2 rounded-lg bg-slate-900 border border-slate-800">
                <i class="fa-solid fa-xmark text-base"></i>
            </button>
        </div>

        <div id="drawerContent" class="p-6 space-y-6 flex-1 overflow-y-auto custom-scrollbar text-xs">
            <!-- Loaded dynamically -->
        </div>

        <div class="p-4 border-t border-slate-800 bg-sidebg flex justify-end">
            <button onclick="closeRightDrawer()" class="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded-xl text-xs transition">
                Fechar Painel
            </button>
        </div>
    </aside>

    <script>
        let currentUser = null;
        let cachedAudits = [];
        let cachedOperators = [];
        let cxDonutChartInst = null;
        let cxBarChartInst = null;
        let riskBarChartInst = null;

        function authFetch(url, options = {}) {
            if (!options.headers) options.headers = {};
            const sessionId = localStorage.getItem('auditai_session');
            if (sessionId) {
                options.headers['X-Session-ID'] = sessionId;
            }
            return fetch(url, options);
        }

        async function quickFill(user, pass) {
            document.getElementById('loginUsername').value = user;
            document.getElementById('loginPassword').value = pass;
            await doLogin(user, pass);
        }

        async function handleLogin(e) {
            if (e) e.preventDefault();
            const u = document.getElementById('loginUsername').value.trim();
            const p = document.getElementById('loginPassword').value.trim();
            await doLogin(u, p);
        }

        async function doLogin(u, p) {
            const err = document.getElementById('loginError');
            err.classList.add('hidden');

            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: u, password: p})
                });
                const data = await res.json();
                if (!res.ok) {
                    err.innerText = data.detail || 'Usuário ou senha inválidos.';
                    err.classList.remove('hidden');
                    return;
                }
                if (data.session_id) {
                    localStorage.setItem('auditai_session', data.session_id);
                }
                currentUser = data.user;
                setupUIForUser();
            } catch(ex) {
                console.error("Erro ao realizar login:", ex);
                err.innerText = 'Erro ao realizar login. Tente novamente.';
                err.classList.remove('hidden');
            }
        }

        async function checkSession() {
            if (window.location.search) {
                window.history.replaceState({}, document.title, window.location.pathname);
            }
            try {
                const res = await authFetch('/api/me');
                if (res.ok) {
                    const data = await res.json();
                    currentUser = data.user;
                    setupUIForUser();
                }
            } catch(e){}
        }

        function setupUIForUser() {
            if (!currentUser) return;
            document.getElementById('loginView').classList.add('hidden');
            document.getElementById('appView').classList.remove('hidden');

            document.getElementById('userName').innerText = currentUser.name || currentUser.username;
            document.getElementById('userRoleBadge').innerText = currentUser.role.toUpperCase();

            // Tab permissions
            const navInfra = document.getElementById('navInfra');
            const navAdmin = document.getElementById('navAdminPerm');

            navInfra.classList.toggle('hidden', !currentUser.can_access_infra);
            navAdmin.classList.toggle('hidden', currentUser.role !== 'admin');

            switchView('dashboard');
            refreshData();
        }

        async function handleLogout() {
            await authFetch('/api/logout', {method: 'POST'});
            localStorage.removeItem('auditai_session');
            currentUser = null;
            document.getElementById('appView').classList.add('hidden');
            document.getElementById('loginView').classList.remove('hidden');
        }

        function switchView(viewName) {
            if (!currentUser) return;
            if (viewName === 'infra' && !currentUser.can_access_infra) return;
            if (viewName === 'admin_perm' && currentUser.role !== 'admin') return;

            const views = ['dashboard', 'operators', 'audits', 'assessments', 'infra', 'admin_perm'];
            views.forEach(v => {
                const el = document.getElementById('view' + v.charAt(0).toUpperCase() + v.slice(1));
                if (el) el.classList.toggle('hidden', v !== viewName);
            });

            // Update nav active classes
            const navs = {
                'dashboard': 'navDashboard',
                'operators': 'navOperators',
                'audits': 'navAudits',
                'assessments': 'navAssessments',
                'infra': 'navInfra',
                'admin_perm': 'navAdminPerm'
            };

            const titles = {
                'dashboard': ['Dashboard Overview', 'Acompanhe métricas de qualidade, conformidade e gestão de riscos em tempo real.'],
                'operators': ['Lista de Operadores', 'Desempenho individual, ranking e notas por atendente.'],
                'audits': ['Auditorias & Chamadas', 'Consulta completa dos 309 atendimentos auditados.'],
                'assessments': ['Avaliações & Analytics', 'Análise profunda por dimensão de qualidade CX.'],
                'infra': ['Infraestrutura & FinOps', 'Custos, consumo de tokens e capacidade da arquitetura.'],
                'admin_perm': ['Gestão de Acessos', 'Gerenciamento de permissões para Administrador e Usuários.']
            };

            if (titles[viewName]) {
                document.getElementById('pageTitle').innerText = titles[viewName][0];
                document.getElementById('pageSubTitle').innerText = titles[viewName][1];
            }

            Object.keys(navs).forEach(k => {
                const btn = document.getElementById(navs[k]);
                if (btn) {
                    if (k === viewName) {
                        btn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-white bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 font-bold transition';
                    } else {
                        btn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/60 font-medium transition';
                    }
                }
            });

            if (viewName === 'admin_perm') loadPermissionsTable();
            if (viewName === 'operators') fetchOperators();
            if (viewName === 'assessments') renderAssessmentsCharts();
        }

        async function refreshData() {
            fetchKPIs();
            fetchFinOps();
            fetchAudits();
            fetchOperators();
        }

        async function fetchKPIs() {
            const res = await authFetch('/api/kpis');
            const data = await res.json();
            document.getElementById('exec-audits').innerText = data.total_audits;
            document.getElementById('exec-score').innerText = data.avg_score;
            document.getElementById('exec-risks').innerText = data.high_risks;
            document.getElementById('infra-tokens').innerText = (data.total_tokens / 1000000).toFixed(1) + 'M';
        }

        async function fetchFinOps() {
            const res = await authFetch('/api/finops');
            if (!res.ok) return;
            const data = await res.json();
            const s = data.summary;
            const proj = data.projections;

            document.getElementById('infra-actual').innerText = `R$ ${s.actual_cost_brl.toFixed(2)}`;
            document.getElementById('infra-equivalent').innerText = `R$ ${s.equivalent_cost_brl.toFixed(2)}`;
            document.getElementById('infra-savings').innerText = `R$ ${s.savings_brl.toFixed(2)}`;

            const tbody = document.getElementById('infra-proj-body');
            tbody.innerHTML = '';
            Object.values(proj).forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="px-4 py-3 font-bold text-white">${p.monthly_calls.toLocaleString()} chamadas/mês</td>
                    <td class="px-4 py-3 text-slate-300">${p.projected_input_tokens.toLocaleString()}</td>
                    <td class="px-4 py-3 text-slate-300">${p.projected_output_tokens.toLocaleString()}</td>
                    <td class="px-4 py-3 text-purple-300 font-mono">${p.projected_total_tokens.toLocaleString()}</td>
                    <td class="px-4 py-3 text-amber-300 font-mono">US$ ${p.equivalent_cost_usd.toLocaleString()}</td>
                    <td class="px-4 py-3 text-emerald-400 font-bold font-mono">R$ ${p.equivalent_cost_brl.toLocaleString()}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function fetchAudits() {
            const res = await authFetch('/api/audits');
            cachedAudits = await res.json();
            renderExecTable(cachedAudits);
            renderHomePreview(cachedAudits);
            renderCXDonutChart(cachedAudits);
        }

        async function fetchOperators() {
            const res = await authFetch('/api/operators');
            if (res.ok) {
                cachedOperators = await res.json();
                renderOperatorsTable(cachedOperators);
            }
        }

        function renderHomePreview(audits) {
            const tbody = document.getElementById('home-audits-preview');
            const alertsList = document.getElementById('home-alerts-list');
            const activityList = document.getElementById('home-activity-list');
            
            tbody.innerHTML = '';
            alertsList.innerHTML = '';
            activityList.innerHTML = '';

            const topSample = audits.slice(0, 5);
            topSample.forEach(a => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/40 transition";
                const risk = a.risk_level || 'Baixo';
                let riskBadge = 'bg-slate-800 text-slate-300';
                if (risk === 'Alto' || risk === 'Crítico') riskBadge = 'bg-rose-500/20 text-rose-300 border border-rose-500/30';

                tr.innerHTML = `
                    <td class="py-3 px-3 font-mono text-indigo-300">${a.protocol_number || 'N/A'}</td>
                    <td class="py-3 px-3 font-medium text-white">${a.operator_name || 'Operador'}</td>
                    <td class="py-3 px-3 font-bold text-emerald-400">${a.overall_score}</td>
                    <td class="py-3 px-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${riskBadge}">${risk}</span></td>
                    <td class="py-3 px-3 text-right">
                        <button onclick='openRightDrawer(${JSON.stringify(a).replace(/'/g, "&apos;")})' class="text-[11px] bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white px-2.5 py-1 rounded-lg font-bold transition">
                            Inspecionar
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

            // High risk alerts
            const highRisks = audits.filter(a => a.risk_level === 'Alto' || a.risk_level === 'Crítico').slice(0, 4);
            if (highRisks.length === 0) {
                alertsList.innerHTML = '<p class="text-xs text-slate-500 italic">Nenhum alerta crítico pendente.</p>';
            } else {
                highRisks.forEach(h => {
                    const item = document.createElement('div');
                    item.className = "p-3 rounded-xl bg-slate-900 border border-rose-500/20 flex items-center justify-between text-xs";
                    item.innerHTML = `
                        <div class="flex items-center space-x-3">
                            <span class="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center shrink-0"><i class="fa-solid fa-triangle-exclamation"></i></span>
                            <div>
                                <div class="font-bold text-white">${h.operator_name} • <span class="text-rose-400 font-mono">${h.protocol_number}</span></div>
                                <div class="text-[10px] text-slate-400">${h.root_cause || 'Aderência técnica fora do padrão.'}</div>
                            </div>
                        </div>
                        <button onclick='openRightDrawer(${JSON.stringify(h).replace(/'/g, "&apos;")})' class="text-[10px] bg-rose-500/20 hover:bg-rose-500 text-rose-300 hover:text-white px-2.5 py-1 rounded-lg font-bold transition">Ver</button>
                    `;
                    alertsList.appendChild(item);
                });
            }

            // Recent Activity
            const recent = audits.slice(0, 4);
            recent.forEach(r => {
                const item = document.createElement('div');
                item.className = "p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between text-xs";
                item.innerHTML = `
                    <div class="flex items-center space-x-3">
                        <span class="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center shrink-0"><i class="fa-solid fa-check"></i></span>
                        <div>
                            <div class="font-bold text-white">Auditoria Concluída via <span class="text-purple-300">${r.provider_used || 'Gemini'}</span></div>
                            <div class="text-[10px] text-slate-400">${r.filename} • Score: <strong class="text-emerald-400">${r.overall_score}</strong></div>
                        </div>
                    </div>
                    <span class="text-[10px] text-slate-500">Hoje</span>
                `;
                activityList.appendChild(item);
            });
        }

        function renderCXDonutChart(audits) {
            const high = audits.filter(a => a.overall_score >= 85).length;
            const med = audits.filter(a => a.overall_score >= 70 && a.overall_score < 85).length;
            const low = audits.filter(a => a.overall_score < 70).length;

            document.getElementById('donut-high').innerText = high;
            document.getElementById('donut-med').innerText = med;
            document.getElementById('donut-low').innerText = low;

            const ctx = document.getElementById('cxDonutChart').getContext('2d');
            if (cxDonutChartInst) cxDonutChartInst.destroy();

            cxDonutChartInst = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Conforme (>85)', 'Alerta (70-85)', 'Crítico (<70)'],
                    datasets: [{
                        data: [high, med, low],
                        backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    cutout: '75%'
                }
            });
        }

        function renderOperatorsTable(ops) {
            const tbody = document.getElementById('operatorsTableBody');
            tbody.innerHTML = '';

            ops.forEach(op => {
                let badgeClass = 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
                if (op.performance_status === 'Necessita Revisão') badgeClass = 'bg-rose-500/10 text-rose-400 border border-rose-500/20';
                else if (op.performance_status === 'Regular') badgeClass = 'bg-blue-500/10 text-blue-400 border border-blue-500/20';

                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/40 transition";
                tr.innerHTML = `
                    <td class="py-4 px-6 font-bold text-white flex items-center space-x-3">
                        <div class="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 text-indigo-400 flex items-center justify-center font-bold text-xs">
                            ${op.operator_name.charAt(0)}
                        </div>
                        <span>${op.operator_name}</span>
                    </td>
                    <td class="py-4 px-6 text-slate-300 font-mono">${op.total_calls} atendimentos</td>
                    <td class="py-4 px-6 font-bold text-emerald-400 font-mono">${op.avg_score} / 100</td>
                    <td class="py-4 px-6 text-rose-400 font-mono">${op.high_risks} casos</td>
                    <td class="py-4 px-6"><span class="px-2.5 py-1 rounded-lg text-[10px] font-bold ${badgeClass}">${op.performance_status}</span></td>
                    <td class="py-4 px-6 text-right">
                        <button onclick="filterAuditsByOperator('${op.operator_name}')" class="text-xs bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white px-3 py-1.5 rounded-xl font-bold transition">
                            Ver Chamadas
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function filterAuditsByOperator(name) {
            switchView('audits');
            document.getElementById('execSearch').value = name;
            filterExecTable();
        }

        function filterExecTable() {
            const search = document.getElementById('execSearch').value.toLowerCase();
            const risk = document.getElementById('execFilterRisk').value;

            const filtered = cachedAudits.filter(a => {
                const matchSearch = (a.protocol_number || '').toLowerCase().includes(search) || 
                                    (a.operator_name || '').toLowerCase().includes(search) ||
                                    (a.filename || '').toLowerCase().includes(search);
                const matchRisk = risk === 'ALL' || a.risk_level === risk;
                return matchSearch && matchRisk;
            });
            renderExecTable(filtered);
        }

        function renderExecTable(audits) {
            const tbody = document.getElementById('exec-table-body');
            tbody.innerHTML = '';

            if (audits.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-slate-500">Nenhum registro encontrado.</td></tr>';
                return;
            }

            audits.forEach(a => {
                const risk = a.risk_level || 'Baixo';
                let scoreBadge = 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
                if (a.overall_score < 70) scoreBadge = 'bg-rose-500/10 text-rose-400 border border-rose-500/20';
                else if (a.overall_score < 85) scoreBadge = 'bg-amber-500/10 text-amber-400 border border-amber-500/20';

                let riskBadge = 'bg-slate-800 text-slate-300 border border-slate-700';
                if (risk === 'Alto' || risk === 'Crítico') riskBadge = 'bg-rose-500/20 text-rose-300 border border-rose-500/30 font-bold';

                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/40 transition";
                tr.innerHTML = `
                    <td class="px-6 py-4 font-mono text-xs text-indigo-300">
                        <div>${a.protocol_number || 'PROT-309112'}</div>
                        <div class="text-[10px] text-slate-500">${a.filename}</div>
                    </td>
                    <td class="px-6 py-4 font-medium text-white">${a.operator_name || 'Operador'}</td>
                    <td class="px-6 py-4 text-slate-300">${a.client_name || 'Cliente Banco Engineer AI'}</td>
                    <td class="px-6 py-4"><span class="px-3 py-1 rounded-full text-xs font-bold ${scoreBadge}">${a.overall_score}</span></td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-lg text-xs ${riskBadge}">${risk}</span></td>
                    <td class="px-6 py-4"><span class="text-xs px-2 py-1 rounded bg-slate-800 text-purple-300 border border-purple-500/30">${a.provider_used || 'Gemini'}</span></td>
                    <td class="px-6 py-4 text-right">
                        <button onclick='openRightDrawer(${JSON.stringify(a).replace(/'/g, "&apos;")})' class="text-xs bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white px-3.5 py-1.5 rounded-xl font-bold transition">
                            Inspecionar
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function renderAssessmentsCharts() {
            if (cachedAudits.length === 0) return;

            let avgCX = 0, avgOp = 0, avgTech = 0, avgBeh = 0;
            cachedAudits.forEach(a => {
                avgCX += (a.cx_score || a.overall_score || 80);
                avgOp += (a.operator_quality_score || a.overall_score || 80);
                avgTech += (a.technical_score || a.overall_score || 80);
                avgBeh += (a.behavioral_score || a.overall_score || 80);
            });
            const len = cachedAudits.length;
            avgCX = (avgCX / len).toFixed(1);
            avgOp = (avgOp / len).toFixed(1);
            avgTech = (avgTech / len).toFixed(1);
            avgBeh = (avgBeh / len).toFixed(1);

            const ctx1 = document.getElementById('cxBarChart').getContext('2d');
            if (cxBarChartInst) cxBarChartInst.destroy();
            cxBarChartInst = new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: ['CX Cliente', 'Qualidade Operador', 'Aderência Técnica', 'Tom Comportamental'],
                    datasets: [{
                        label: 'Score Médio',
                        data: [avgCX, avgOp, avgTech, avgBeh],
                        backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6'],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { y: { min: 0, max: 100 } }
                }
            });

            const passCount = cachedAudits.filter(a => a.overall_score >= 75).length;
            const failCount = cachedAudits.length - passCount;

            const ctx2 = document.getElementById('riskBarChart').getContext('2d');
            if (riskBarChartInst) riskBarChartInst.destroy();
            riskBarChartInst = new Chart(ctx2, {
                type: 'bar',
                data: {
                    labels: ['Resultado Global Auditoria'],
                    datasets: [
                        { label: 'Aprovados (>=75)', data: [passCount], backgroundColor: '#10b981', borderRadius: 8 },
                        { label: 'Com Alerta/Risco (<75)', data: [failCount], backgroundColor: '#ef4444', borderRadius: 8 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { x: { stacked: true }, y: { stacked: true } }
                }
            });
        }

        // OPEN SLIDE-OVER RIGHT DRAWER (Behance Image 4)
        function openRightDrawer(audit) {
            document.getElementById('drawerTitle').innerText = audit.filename;
            document.getElementById('drawerSubTitle').innerText = `Protocolo: ${audit.protocol_number || 'N/A'} • Operador: ${audit.operator_name || 'Operador'}`;

            const cxScore = audit.cx_score !== undefined ? audit.cx_score : Math.round(audit.overall_score || 85);
            const opQuality = audit.operator_quality_score !== undefined ? audit.operator_quality_score : Math.round(audit.overall_score || 80);
            const techScore = audit.technical_score !== undefined ? audit.technical_score : Math.round(audit.overall_score || 82);
            const behScore = audit.behavioral_score !== undefined ? audit.behavioral_score : Math.round(audit.overall_score || 88);

            let risksList = [];
            if (Array.isArray(audit.identified_risks)) {
                risksList = audit.identified_risks;
            } else if (typeof audit.identified_risks === 'string') {
                try { risksList = JSON.parse(audit.identified_risks); } catch(e) { risksList = [audit.identified_risks]; }
            }

            const risksBadges = risksList.length > 0 
                ? risksList.map(r => `<span class="px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/20 text-xs">${r}</span>`).join(' ')
                : `<span class="text-slate-400 text-xs italic">Nenhum risco crítico identificado nesta transcrição.</span>`;

            const fullText = audit.transcricao_original || "Transcrição de áudio em processamento no banco de dados.";
            const formattedLines = fullText.split(String.fromCharCode(10)).map(line => {
                const trimmed = line.trim();
                if (!trimmed) return '';
                if (trimmed.toLowerCase().startsWith('atendente:') || trimmed.toLowerCase().startsWith('operador:')) {
                    return `<div class="bg-indigo-950/40 border-l-4 border-indigo-500 p-3 rounded-r-xl text-xs text-indigo-200"><strong class="text-indigo-400 block mb-1">OPERADOR</strong> ${trimmed.substring(trimmed.indexOf(':')+1)}</div>`;
                } else if (trimmed.toLowerCase().startsWith('cliente:')) {
                    return `<div class="bg-slate-900 border-l-4 border-blue-500 p-3 rounded-r-xl text-xs text-slate-200"><strong class="text-blue-400 block mb-1">CLIENTE</strong> ${trimmed.substring(trimmed.indexOf(':')+1)}</div>`;
                }
                return `<div class="bg-slate-950 p-2.5 rounded-lg text-xs text-slate-300 font-mono">${trimmed}</div>`;
            }).filter(Boolean).join('');

            const content = document.getElementById('drawerContent');
            content.innerHTML = `
                <!-- Top Metric Cards -->
                <div class="grid grid-cols-2 gap-3">
                    <div class="bg-slate-900 p-4 rounded-xl border border-slate-800 text-center">
                        <span class="text-[10px] text-slate-400 uppercase font-bold">Score Geral</span>
                        <div class="text-2xl font-extrabold text-emerald-400 mt-1">${audit.overall_score}</div>
                    </div>
                    <div class="bg-slate-900 p-4 rounded-xl border border-slate-800 text-center">
                        <span class="text-[10px] text-slate-400 uppercase font-bold">Nível de Risco</span>
                        <div class="text-xl font-extrabold ${audit.risk_level === 'Baixo' ? 'text-emerald-400' : 'text-rose-400'} mt-1">${audit.risk_level || 'Baixo'}</div>
                    </div>
                </div>

                <!-- 1-Click Audio Transcript Accordion Button -->
                <button onclick="toggleDrawerTranscript()" class="w-full py-3 bg-indigo-600/20 hover:bg-indigo-600 border border-indigo-500/30 text-indigo-300 hover:text-white rounded-xl font-extrabold transition flex items-center justify-center gap-2">
                    <i class="fa-solid fa-comments"></i>
                    <span id="drawerBtnTransText">💬 Ver Transcrição Íntegra (1-Click)</span>
                </button>

                <!-- Transcript Box -->
                <div id="drawerTranscriptBox" class="hidden space-y-2 max-h-80 overflow-y-auto bg-black p-4 rounded-xl border border-indigo-500/30 font-mono custom-scrollbar">
                    ${formattedLines}
                </div>

                <!-- CX Scorecard 4D Progress Bars -->
                <div class="bg-slate-900 p-4 rounded-xl border border-slate-800 space-y-3">
                    <h4 class="font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-chart-line text-indigo-400"></i> Scorecard Pydantic 4D
                    </h4>
                    <div class="space-y-2">
                        <div>
                            <div class="flex justify-between font-semibold"><span>🎯 Experiência CX</span><span class="text-emerald-400 font-mono">${cxScore}/100</span></div>
                            <div class="w-full bg-slate-800 h-2 rounded-full mt-1"><div class="bg-emerald-500 h-2 rounded-full" style="width: ${cxScore}%"></div></div>
                        </div>
                        <div>
                            <div class="flex justify-between font-semibold"><span>👔 Qualidade Operador</span><span class="text-blue-400 font-mono">${opQuality}/100</span></div>
                            <div class="w-full bg-slate-800 h-2 rounded-full mt-1"><div class="bg-blue-500 h-2 rounded-full" style="width: ${opQuality}%"></div></div>
                        </div>
                        <div>
                            <div class="flex justify-between font-semibold"><span>⚙️ Aderência Técnica</span><span class="text-amber-400 font-mono">${techScore}/100</span></div>
                            <div class="w-full bg-slate-800 h-2 rounded-full mt-1"><div class="bg-amber-500 h-2 rounded-full" style="width: ${techScore}%"></div></div>
                        </div>
                        <div>
                            <div class="flex justify-between font-semibold"><span>💬 Tom & Empatia</span><span class="text-purple-400 font-mono">${behScore}/100</span></div>
                            <div class="w-full bg-slate-800 h-2 rounded-full mt-1"><div class="bg-purple-500 h-2 rounded-full" style="width: ${behScore}%"></div></div>
                        </div>
                    </div>
                </div>

                <!-- Risk Analysis & Root Cause -->
                <div class="bg-slate-900 p-4 rounded-xl border border-slate-800 space-y-2">
                    <h4 class="font-bold text-white">Análise de Risco & Causa Raiz</h4>
                    <p class="text-slate-300"><strong>Causa Raiz:</strong> <span class="text-amber-300">${audit.root_cause || 'Não identificado'}</span></p>
                    <p class="text-slate-300"><strong>Responsável:</strong> <span class="text-indigo-300">${audit.problem_owner || 'Não identificado'}</span></p>
                    <div class="pt-1"><strong class="text-slate-400 block mb-1">Riscos Identificados:</strong> ${risksBadges}</div>
                </div>

                <!-- Executive Summary -->
                <div class="bg-slate-900 p-4 rounded-xl border border-slate-800 space-y-2">
                    <h4 class="font-bold text-white">Resumo Executivo do Atendimento</h4>
                    <p class="text-slate-200 leading-relaxed">${audit.executive_summary}</p>
                </div>

                <!-- Literal Evidence Quote -->
                <div class="bg-slate-900 p-4 rounded-xl border border-indigo-500/30 space-y-2">
                    <h4 class="font-bold text-indigo-400">Citação Literal da Evidência Extraída</h4>
                    <p class="italic text-slate-300 bg-black p-3 rounded-lg border border-slate-800 font-mono">"${audit.evidence_quote || 'Evidência confirmada na gravação.'}"</p>
                </div>
            `;

            document.getElementById('rightDrawerOverlay').classList.remove('hidden');
            document.getElementById('rightDrawer').classList.remove('translate-x-full');
        }

        function toggleDrawerTranscript() {
            const box = document.getElementById('drawerTranscriptBox');
            const btn = document.getElementById('drawerBtnTransText');
            if (box.classList.contains('hidden')) {
                box.classList.remove('hidden');
                btn.innerText = '🔼 Ocultar Transcrição';
            } else {
                box.classList.add('hidden');
                btn.innerText = '💬 Ver Transcrição Íntegra (1-Click)';
            }
        }

        function closeRightDrawer() {
            document.getElementById('rightDrawer').classList.add('translate-x-full');
            document.getElementById('rightDrawerOverlay').classList.add('hidden');
        }

        function handleGlobalSearch() {
            const query = document.getElementById('globalSearch').value.toLowerCase();
            switchView('audits');
            document.getElementById('execSearch').value = query;
            filterExecTable();
        }

        async function loadPermissionsTable() {
            const res = await authFetch('/api/admin/permissions');
            if (!res.ok) return;
            const users = await res.json();
            const tbody = document.getElementById('permTableBody');
            tbody.innerHTML = '';

            users.forEach(u => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="px-6 py-4 font-bold text-white">${u.name} <span class="text-xs text-slate-500">(${u.username})</span></td>
                    <td class="px-6 py-4"><span class="px-2.5 py-0.5 rounded text-xs font-bold ${u.role === 'admin' ? 'bg-indigo-500/20 text-indigo-400' : 'bg-blue-500/20 text-blue-400'}">${u.role.toUpperCase()}</span></td>
                    <td class="px-6 py-4 text-center">
                        <input type="checkbox" id="perm_infra_${u.username}" ${u.can_access_infra ? 'checked' : ''} ${u.username === 'admin' ? 'disabled' : ''} class="w-4 h-4 rounded text-indigo-500">
                    </td>
                    <td class="px-6 py-4 text-center">
                        <input type="checkbox" id="perm_exec_${u.username}" ${u.can_access_executive ? 'checked' : ''} class="w-4 h-4 rounded text-indigo-500">
                    </td>
                    <td class="px-6 py-4 text-right">
                        <button onclick="saveUserPermission('${u.username}')" class="text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-xl font-bold transition">
                            Salvar
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function saveUserPermission(username) {
            const inf = document.getElementById(`perm_infra_${username}`).checked;
            const exc = document.getElementById(`perm_exec_${username}`).checked;

            const res = await authFetch('/api/admin/permissions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: username, can_access_infra: inf, can_access_executive: exc})
            });
            if (res.ok) alert(`Permissões atualizadas com sucesso para o usuário '${username}'!`);
        }

        checkSession();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def get_root():
    return HTML_PAGE

@app.post("/api/login")
def login_api(data: Dict[str, Any], response: Response):
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    print(f"[LOGIN DEBUG] Tentativa de login: username='{username}'")
    user = db.authenticate_user(username, password)
    if not user:
        print(f"[LOGIN DEBUG] Falha: usuário ou senha incorretos para '{username}'")
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos. Tente 'admin'/'admin1' ou 'usuario'/'usuario1'.")
    
    session_id = os.urandom(16).hex()
    db.create_session(session_id, user["username"])
    response.set_cookie(key="auditai_session", value=session_id, httponly=True, path="/", samesite="lax")
    print(f"[LOGIN DEBUG] SUCESSO: Login realizado para '{username}' (role={user['role']})")
    return {"status": "ok", "user": user, "session_id": session_id}

@app.post("/api/logout")
def logout_api(request: Request, response: Response):
    session_id = request.cookies.get("auditai_session") or request.headers.get("X-Session-ID")
    if session_id:
        db.delete_session(session_id)
    response.delete_cookie("auditai_session", path="/")
    return {"status": "ok"}

@app.get("/api/me")
def me_api(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    return {"user": user}

@app.get("/api/admin/permissions")
def get_permissions(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao Administrador.")
    return db.get_all_users_permissions()

@app.post("/api/admin/permissions")
def update_permissions(data: Dict[str, Any], user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao Administrador.")
    target_user = data.get("username")
    can_infra = data.get("can_access_infra", True)
    can_exec = data.get("can_access_executive", True)
    
    success = db.update_user_permissions(target_user, can_infra, can_exec)
    if not success:
        raise HTTPException(status_code=400, detail="Could not update permissions.")
    return {"status": "ok"}

@app.get("/api/kpis")
def get_kpis():
    return db.get_kpi_summary()

@app.get("/api/operators")
def get_operators(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    return db.get_operators_summary()

@app.get("/api/finops")
def get_finops(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if not user or not user.get("can_access_infra", False):
        raise HTTPException(status_code=403, detail="Acesso restrito à equipe de Infraestrutura/FinOps.")
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
    return db.get_all_audits(limit=309)

@app.get("/api/audit/{audit_id}")
def get_single_audit(audit_id: int):
    audits = db.get_all_audits(limit=500)
    for a in audits:
        if a["id"] == audit_id:
            return a
    raise HTTPException(status_code=404, detail="Audit not found")

if __name__ == "__main__":
    import uvicorn
    print("Iniciando Web Dashboard AuditAI em: http://127.0.0.1:8080")
    uvicorn.run("web_dashboard:app", host="127.0.0.1", port=8080, reload=False)
