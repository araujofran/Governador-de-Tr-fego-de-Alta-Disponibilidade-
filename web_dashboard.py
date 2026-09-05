import os
import json
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Response, Depends, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from database import AuditDatabase
from finops_engine import FinOpsEngine

logger = logging.getLogger("TrafficController.WebDashboard")

app = FastAPI(title="AuditAI - Banco Engineer AI SaaS Dashboard & LLM Traffic Controller")
db = AuditDatabase()
finops_engine = FinOpsEngine()

# Session store in memory (for simplicity and speed)
SESSIONS: Dict[str, Dict[str, Any]] = {}

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    session_id = request.cookies.get("auditai_session")
    if session_id and session_id in SESSIONS:
        return SESSIONS[session_id]
    return None

HTML_PAGE = """<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuditAI — Inteligência que Protege o Seu Negócio | Banco Engineer AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400;1,600&family=Caveat:wght@600&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
                        cursive: ['"Caveat"', 'cursive']
                    },
                    colors: {
                        gold: {
                            400: '#fbbf24',
                            500: '#f59e0b',
                            600: '#d97706',
                        },
                        darkbg: '#0b0f17',
                        cardbg: '#131926',
                        borderbg: '#1e293b'
                    }
                }
            }
        }
    </script>
    <style>
        .gold-gradient-btn {
            background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
        }
        .gold-gradient-btn:hover {
            background: linear-gradient(135deg, #facc15 0%, #d97706 100%);
        }
        .glass-panel {
            background: rgba(19, 25, 38, 0.85);
            backdrop-filter: blur(16px);
        }
    </style>
</head>
<body class="bg-darkbg text-slate-100 min-h-screen font-sans antialiased selection:bg-amber-500 selection:text-black">

    <!-- LOGIN SCREEN CONTAINER (Renders if not logged in) -->
    <div id="loginView" class="min-h-screen flex items-center justify-center p-4 md:p-8 bg-gradient-to-br from-darkbg via-[#0c121e] to-darkbg">
        <div class="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            
            <!-- Left Column: Hero & Branding Showcase -->
            <div class="lg:col-span-7 space-y-8 p-4 lg:p-8">
                <!-- Top Header -->
                <div class="flex items-center space-x-3">
                    <div class="flex items-center space-x-1.5">
                        <div class="w-2 h-6 bg-gradient-to-b from-amber-400 to-amber-600 rounded-full"></div>
                        <div class="w-2 h-9 bg-gradient-to-b from-amber-400 to-amber-600 rounded-full"></div>
                        <div class="w-2 h-5 bg-gradient-to-b from-amber-400 to-amber-600 rounded-full"></div>
                        <div class="w-2 h-7 bg-gradient-to-b from-amber-400 to-amber-600 rounded-full"></div>
                    </div>
                    <div>
                        <div class="text-2xl font-extrabold tracking-tight text-white flex items-center gap-2">
                            <span>AuditAI</span>
                        </div>
                        <div class="text-[10px] font-semibold tracking-widest text-slate-400 uppercase">Inteligência que Protege o Seu Negócio</div>
                    </div>
                    <div class="ml-auto flex items-center space-x-2 text-xs bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700/60">
                        <span class="text-slate-400">Versão 1.0.0</span>
                        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                        <span class="text-emerald-400 font-semibold">Sistema online</span>
                    </div>
                </div>

                <!-- Main Headline -->
                <div class="space-y-4">
                    <h1 class="text-4xl md:text-5xl font-extrabold text-white leading-tight">
                        Da conversa ao <br>
                        <span class="text-transparent bg-clip-text bg-gradient-to-r from-amber-300 via-amber-400 to-amber-600">compliance.</span>
                    </h1>
                    <p class="text-slate-400 text-base max-w-lg leading-relaxed">
                        Transforme atendimentos em insights, reduza riscos e fortaleça a qualidade com o poder da IA no <strong class="text-slate-200">Banco Engineer AI</strong>.
                    </p>
                </div>

                <!-- Feature Badges -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div class="flex items-start space-x-3 p-3.5 rounded-xl bg-cardbg/60 border border-slate-800">
                        <div class="p-2.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                        </div>
                        <div>
                            <div class="text-sm font-bold text-white">Auditoria automatizada</div>
                            <div class="text-xs text-slate-400">Analise 100% dos atendimentos</div>
                        </div>
                    </div>

                    <div class="flex items-start space-x-3 p-3.5 rounded-xl bg-cardbg/60 border border-slate-800">
                        <div class="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
                        </div>
                        <div>
                            <div class="text-sm font-bold text-white">Insights reais</div>
                            <div class="text-xs text-slate-400">Qualidade, riscos e oportunidades</div>
                        </div>
                    </div>

                    <div class="flex items-start space-x-3 p-3.5 rounded-xl bg-cardbg/60 border border-slate-800">
                        <div class="p-2.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                        </div>
                        <div>
                            <div class="text-sm font-bold text-white">Mais eficiência</div>
                            <div class="text-xs text-slate-400">Com menos esforço e mais resultado</div>
                        </div>
                    </div>

                    <div class="flex items-start space-x-3 p-3.5 rounded-xl bg-cardbg/60 border border-slate-800">
                        <div class="p-2.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                        </div>
                        <div>
                            <div class="text-sm font-bold text-white">Seus dados, seguros</div>
                            <div class="text-xs text-slate-400">Privacidade e conformidade em primeiro lugar</div>
                        </div>
                    </div>
                </div>

                <!-- Floating Interactive Sample & Quote -->
                <div class="relative bg-gradient-to-r from-cardbg via-slate-900 to-cardbg border border-slate-800 rounded-2xl p-5 shadow-2xl">
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                            <span class="w-2 h-2 rounded-full bg-amber-400"></span> Atendimento analisado ✓
                        </span>
                        <span class="text-[10px] text-slate-400">Banco Engineer AI</span>
                    </div>
                    <div class="grid grid-cols-4 gap-2 text-center text-xs">
                        <div class="bg-slate-800/80 p-2 rounded-lg border border-slate-700">
                            <div class="text-[10px] text-slate-400">Qualidade</div>
                            <div class="text-base font-extrabold text-emerald-400">92</div>
                        </div>
                        <div class="bg-slate-800/80 p-2 rounded-lg border border-slate-700">
                            <div class="text-[10px] text-slate-400">Risco</div>
                            <div class="text-base font-extrabold text-blue-400">baixo</div>
                        </div>
                        <div class="bg-slate-800/80 p-2 rounded-lg border border-slate-700">
                            <div class="text-[10px] text-slate-400">Compliance</div>
                            <div class="text-base font-extrabold text-amber-400">OK</div>
                        </div>
                        <div class="bg-slate-800/80 p-2 rounded-lg border border-slate-700">
                            <div class="text-[10px] text-slate-400">Cliente</div>
                            <div class="text-base font-extrabold text-purple-300">satisfeito</div>
                        </div>
                    </div>

                    <div class="mt-4 pt-3 border-t border-slate-800 text-xs italic text-slate-400 flex items-center justify-between">
                        <span>"Qualidade não é um ato. É um hábito, e agora, é escalável."</span>
                        <span class="font-cursive text-amber-300 text-lg not-italic">Conversas melhores, negócios maiores</span>
                    </div>
                </div>
            </div>

            <!-- Right Column: Login Card -->
            <div class="lg:col-span-5">
                <div class="glass-panel border border-slate-700/60 rounded-3xl p-8 shadow-2xl space-y-6">
                    
                    <div class="text-center space-y-2">
                        <div class="inline-flex items-center space-x-1.5 mb-2">
                            <div class="w-2 h-6 bg-gradient-to-b from-amber-400 to-amber-600 rounded-full"></div>
                            <div class="w-2 h-9 bg-gradient-to-b from-amber-400 to-amber-600 rounded-full"></div>
                            <div class="w-2 h-5 bg-gradient-to-b from-amber-400 to-amber-600 rounded-full"></div>
                        </div>
                        <h2 class="text-2xl font-extrabold text-white">Bem-vindo de volta!</h2>
                        <p class="text-xs text-slate-400">Faça login para acessar sua plataforma.</p>
                    </div>

                    <form id="loginForm" onsubmit="handleLogin(event)" class="space-y-4">
                        <div>
                            <label class="block text-xs font-semibold text-slate-300 mb-1.5">Seu e-mail ou usuário</label>
                            <div class="relative">
                                <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"></path></svg>
                                </span>
                                <input type="text" id="loginUsername" required placeholder="admin@engineer.ai ou usuario@engineer.ai" class="w-full pl-10 pr-4 py-3 bg-slate-900/90 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400 transition placeholder:text-slate-600">
                            </div>
                        </div>

                        <div>
                            <label class="block text-xs font-semibold text-slate-300 mb-1.5">Sua senha</label>
                            <div class="relative">
                                <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                                </span>
                                <input type="password" id="loginPassword" required placeholder="••••••••" class="w-full pl-10 pr-4 py-3 bg-slate-900/90 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400 transition placeholder:text-slate-600">
                            </div>
                        </div>

                        <div class="flex items-center justify-between text-xs text-slate-400">
                            <label class="flex items-center space-x-2 cursor-pointer">
                                <input type="checkbox" checked class="rounded bg-slate-900 border-slate-700 text-amber-500 focus:ring-amber-400">
                                <span>Lembrar de mim</span>
                            </label>
                            <a href="#" onclick="alert('Credenciais padrão:\nADMIN -> Login: admin | Senha: admin1\nUSUÁRIO -> Login: usuario | Senha: usuario1')" class="text-amber-400 hover:underline">Esqueceu sua senha?</a>
                        </div>

                        <div id="loginError" class="text-xs text-rose-400 font-semibold hidden bg-rose-500/10 p-2.5 rounded-lg border border-rose-500/20 text-center"></div>

                        <button type="submit" class="w-full py-3.5 font-bold text-slate-950 rounded-xl gold-gradient-btn transition shadow-lg flex items-center justify-center space-x-2 text-sm tracking-wide">
                            <span>Entrar</span>
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                        </button>
                    </form>

                    <div class="relative flex py-2 items-center">
                        <div class="flex-grow border-t border-slate-800"></div>
                        <span class="flex-shrink mx-4 text-xs text-slate-500">ou</span>
                        <div class="flex-grow border-t border-slate-800"></div>
                    </div>

                    <button onclick="quickFill('admin', 'admin1')" class="w-full py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 text-xs font-medium rounded-xl transition flex items-center justify-center space-x-2">
                        <span>Entrar com Google (Demonstração Admin)</span>
                    </button>

                    <div class="text-center text-xs text-slate-500 pt-2">
                        Ainda não tem uma conta? <a href="#" class="text-amber-400 hover:underline font-semibold">Fale com o administrador</a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- MAIN APP CONTAINER (Rendered when Logged In) -->
    <div id="appView" class="hidden min-h-screen flex flex-col">
        
        <!-- Top App Switcher & User Header -->
        <header class="bg-cardbg border-b border-slate-800 px-6 py-3 flex flex-wrap justify-between items-center sticky top-0 z-50 shadow-lg">
            <div class="flex items-center space-x-6">
                <!-- App Logo -->
                <div class="flex items-center space-x-2">
                    <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-500 to-amber-600 flex items-center justify-center font-bold text-slate-950 text-sm shadow">
                        AI
                    </div>
                    <div>
                        <div class="text-base font-extrabold text-white">AuditAI</div>
                        <div class="text-[10px] text-amber-400 font-semibold">Banco Engineer AI</div>
                    </div>
                </div>

                <!-- Navigation Tabs / Interface Switcher -->
                <nav class="flex items-center space-x-2 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800 text-xs font-semibold" id="navTabs">
                    <button id="tabExecutive" onclick="switchTab('executive')" class="px-4 py-2 rounded-lg text-white bg-amber-500/20 text-amber-300 border border-amber-500/30 transition flex items-center space-x-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z"></path></svg>
                        <span>📊 Dashboard Executivo SaaS</span>
                    </button>
                    <button id="tabInfra" onclick="switchTab('infra')" class="px-4 py-2 rounded-lg text-slate-400 hover:text-white transition flex items-center space-x-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                        <span>⚡ Infraestrutura & FinOps (Dev/Admin)</span>
                    </button>
                    <button id="tabAdmin" onclick="switchTab('admin_perm')" class="px-4 py-2 rounded-lg text-slate-400 hover:text-white transition flex items-center space-x-2 hidden">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                        <span>⚙️ Gestão de Acessos</span>
                    </button>
                </nav>
            </div>

            <!-- Right Profile & Logout -->
            <div class="flex items-center space-x-4 text-xs">
                <div class="flex items-center space-x-2 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800">
                    <span id="userRoleBadge" class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 uppercase">ADMIN</span>
                    <span id="userName" class="text-slate-200 font-medium">Administrador</span>
                </div>
                <button onclick="handleLogout()" class="px-3 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 rounded-xl font-semibold transition flex items-center space-x-1.5">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                    <span>Sair</span>
                </button>
            </div>
        </header>

        <!-- VIEW 1: EXECUTIVE SAAS DASHBOARD (LMS Behance Inspired) -->
        <main id="viewExecutive" class="p-6 max-w-7xl mx-auto space-y-6 flex-grow w-full">
            
            <!-- Hero Banner -->
            <div class="bg-gradient-to-r from-cardbg via-slate-900 to-cardbg border border-slate-800 rounded-3xl p-6 shadow-xl relative overflow-hidden">
                <div class="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 text-xs font-bold border border-amber-500/20 mb-2">
                            <span>Banco Engineer AI • Quality & Compliance Center</span>
                        </div>
                        <h2 class="text-2xl font-extrabold text-white">Painel Executivo de Auditoria de Atendimentos</h2>
                        <p class="text-xs text-slate-400 mt-1">Análise automatizada de conformidade contratual, experiência do cliente e gestão de riscos por IA.</p>
                    </div>
                    <button onclick="refreshData()" class="px-4 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-extrabold rounded-xl transition shadow-lg flex items-center space-x-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                        <span>Atualizar Relatório</span>
                    </button>
                </div>
            </div>

            <!-- Executive KPI Scorecards Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <div class="bg-cardbg rounded-2xl p-5 border border-slate-800 shadow-lg">
                    <div class="flex items-center justify-between text-slate-400 mb-2">
                        <span class="text-xs font-bold uppercase tracking-wider">Média de Qualidade CX</span>
                        <span class="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        </span>
                    </div>
                    <div class="text-3xl font-extrabold text-white" id="exec-score">0.0</div>
                    <div class="text-xs text-emerald-400 mt-2 flex items-center space-x-1">
                        <span>Conformidade contratual global</span>
                    </div>
                </div>

                <div class="bg-cardbg rounded-2xl p-5 border border-slate-800 shadow-lg">
                    <div class="flex items-center justify-between text-slate-400 mb-2">
                        <span class="text-xs font-bold uppercase tracking-wider">Atendimentos Auditados</span>
                        <span class="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                        </span>
                    </div>
                    <div class="text-3xl font-extrabold text-white" id="exec-audits">0</div>
                    <div class="text-xs text-slate-400 mt-2">100% gravados em SQLite</div>
                </div>

                <div class="bg-cardbg rounded-2xl p-5 border border-slate-800 shadow-lg">
                    <div class="flex items-center justify-between text-slate-400 mb-2">
                        <span class="text-xs font-bold uppercase tracking-wider">Alertas de Risco</span>
                        <span class="p-2 rounded-lg bg-rose-500/10 text-rose-400">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                        </span>
                    </div>
                    <div class="text-3xl font-extrabold text-rose-400" id="exec-risks">0</div>
                    <div class="text-xs text-rose-400 mt-2">Grau Alto / Crítico</div>
                </div>

                <div class="bg-cardbg rounded-2xl p-5 border border-slate-800 shadow-lg">
                    <div class="flex items-center justify-between text-slate-400 mb-2">
                        <span class="text-xs font-bold uppercase tracking-wider">Resolutividade</span>
                        <span class="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                        </span>
                    </div>
                    <div class="text-3xl font-extrabold text-amber-400" id="exec-resolutivity">94.2%</div>
                    <div class="text-xs text-slate-400 mt-2">Solução no 1º contato</div>
                </div>
            </div>

            <!-- Main Executive Grid: Call Inspector Table -->
            <div class="bg-cardbg rounded-2xl border border-slate-800 shadow-xl overflow-hidden">
                <div class="p-5 border-b border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h3 class="text-base font-bold text-white">Relatório de Auditorias — Banco Engineer AI</h3>
                        <p class="text-xs text-slate-400">Selecione qualquer atendimento para inspecionar scorecards, evidências por linha e causa raiz.</p>
                    </div>

                    <!-- Search & Filter Controls -->
                    <div class="flex flex-wrap items-center gap-3">
                        <input type="text" id="execSearch" onkeyup="filterExecTable()" placeholder="Buscar operador ou protocolo..." class="px-3.5 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-amber-400 w-60">
                        
                        <select id="execFilterRisk" onchange="filterExecTable()" class="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none">
                            <option value="ALL">Todos os Riscos</option>
                            <option value="Baixo">Risco Baixo</option>
                            <option value="Médio">Risco Médio</option>
                            <option value="Alto">Risco Alto</option>
                            <option value="Crítico">Risco Crítico</option>
                        </select>
                    </div>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-slate-300">
                        <thead class="bg-slate-900/90 text-xs uppercase tracking-wider text-slate-400">
                            <tr>
                                <th class="px-6 py-3.5">Protocolo / Arquivo</th>
                                <th class="px-6 py-3.5">Operador</th>
                                <th class="px-6 py-3.5">Cliente</th>
                                <th class="px-6 py-3.5">Score Final</th>
                                <th class="px-6 py-3.5">Nível de Risco</th>
                                <th class="px-6 py-3.5">Provedor IA</th>
                                <th class="px-6 py-3.5 text-right">Ação</th>
                            </tr>
                        </thead>
                        <tbody id="exec-table-body" class="divide-y divide-slate-800/60 font-sans">
                            <tr><td colspan="7" class="text-center py-8 text-slate-500">Carregando auditorias...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </main>

        <!-- VIEW 2: INFRASTRUCTURE & FINOPS DASHBOARD (Dev/Admin View) -->
        <main id="viewInfra" class="p-6 max-w-7xl mx-auto space-y-6 flex-grow w-full hidden">
            <!-- Developer Telemetry Content -->
            <div class="bg-cardbg rounded-2xl p-6 border border-slate-800 shadow-xl space-y-4">
                <div class="flex justify-between items-center">
                    <div>
                        <h2 class="text-xl font-bold text-white">Governador Multi-Provedor & FinOps LLM</h2>
                        <p class="text-xs text-slate-400">Métricas de infraestrutura, controle de taxa de tokens e planejamento de capacidade.</p>
                    </div>
                    <span class="px-3 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-bold rounded-full">Painel Desenvolvedor</span>
                </div>

                <!-- FinOps Cards -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
                    <div class="bg-slate-900 p-4 rounded-xl border border-slate-800">
                        <div class="text-xs text-slate-400">Custo Real API (Free)</div>
                        <div class="text-2xl font-extrabold text-emerald-400" id="infra-actual">R$ 0,00</div>
                    </div>
                    <div class="bg-slate-900 p-4 rounded-xl border border-slate-800">
                        <div class="text-xs text-slate-400">Custo Comercial Eq.</div>
                        <div class="text-2xl font-extrabold text-amber-400" id="infra-equivalent">R$ 0,00</div>
                    </div>
                    <div class="bg-slate-900 p-4 rounded-xl border border-slate-800">
                        <div class="text-xs text-slate-400">Economia Estimada</div>
                        <div class="text-2xl font-extrabold text-emerald-400" id="infra-savings">R$ 0,00</div>
                    </div>
                    <div class="bg-slate-900 p-4 rounded-xl border border-slate-800">
                        <div class="text-xs text-slate-400">Tokens Totais</div>
                        <div class="text-2xl font-extrabold text-purple-300" id="infra-tokens">0</div>
                    </div>
                </div>

                <!-- Projections Table -->
                <div class="pt-4">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Tabela de Capacity Planning Mensal</h4>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-xs text-slate-300">
                            <thead class="bg-slate-800 text-slate-400">
                                <tr>
                                    <th class="px-4 py-2">Escala Mensal</th>
                                    <th class="px-4 py-2">Tokens Entrada</th>
                                    <th class="px-4 py-2">Tokens Saída</th>
                                    <th class="px-4 py-2">Tokens Totais</th>
                                    <th class="px-4 py-2">Custo Eq. USD</th>
                                    <th class="px-4 py-2">Custo Eq. BRL</th>
                                </tr>
                            </thead>
                            <tbody id="infra-proj-body" class="divide-y divide-slate-800 font-mono">
                                <tr><td colspan="6" class="text-center py-4 text-slate-500">Carregando projeções...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </main>

        <!-- VIEW 3: ADMIN PERMISSIONS MANAGEMENT -->
        <main id="viewAdminPerm" class="p-6 max-w-4xl mx-auto space-y-6 flex-grow w-full hidden">
            <div class="bg-cardbg rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
                <div>
                    <h2 class="text-xl font-bold text-white flex items-center gap-2">
                        <span>⚙️ Painel de Gestão de Acessos e Permissões</span>
                    </h2>
                    <p class="text-xs text-slate-400 mt-1">Como administrador, defina exatamente quais dashboards cada perfil/usuário tem permissão para visualizar.</p>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-slate-300">
                        <thead class="bg-slate-900 text-xs uppercase tracking-wider text-slate-400">
                            <tr>
                                <th class="px-6 py-3.5">Usuário / Perfil</th>
                                <th class="px-6 py-3.5">Função (Role)</th>
                                <th class="px-6 py-3.5 text-center">Dashboard Infra & FinOps</th>
                                <th class="px-6 py-3.5 text-center">Dashboard Executivo SaaS</th>
                                <th class="px-6 py-3.5 text-right">Ação</th>
                            </tr>
                        </thead>
                        <tbody id="permTableBody" class="divide-y divide-slate-800">
                            <tr><td colspan="5" class="text-center py-4 text-slate-500">Carregando usuários...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    </div>

    <!-- AUDIT DETAIL INSPECTOR MODAL -->
    <div id="auditModal" class="fixed inset-0 bg-black/80 backdrop-blur-md z-50 hidden flex items-center justify-center p-4">
        <div class="bg-cardbg border border-slate-800 rounded-3xl max-w-4xl w-full max-h-[92vh] overflow-y-auto shadow-2xl p-6 lg:p-8 relative space-y-6">
            <button onclick="closeModal()" class="absolute top-5 right-5 text-slate-400 hover:text-white p-2 rounded-xl bg-slate-900 border border-slate-800">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
            <div id="modalContent"></div>
        </div>
    </div>

    <script>
        let currentUser = null;
        let cachedAudits = [];

        function quickFill(user, pass) {
            document.getElementById('loginUsername').value = user;
            document.getElementById('loginPassword').value = pass;
            document.getElementById('loginForm').dispatchEvent(new Event('submit'));
        }

        async function handleLogin(e) {
            e.preventDefault();
            const u = document.getElementById('loginUsername').value;
            const p = document.getElementById('loginPassword').value;
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
                currentUser = data.user;
                setupUIForUser();
            } catch(ex) {
                err.innerText = 'Erro ao realizar login. Tente novamente.';
                err.classList.remove('hidden');
            }
        }

        async function checkSession() {
            try {
                const res = await fetch('/api/me');
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
            const btnInfra = document.getElementById('tabInfra');
            const btnExec = document.getElementById('tabExecutive');
            const btnAdmin = document.getElementById('tabAdmin');

            btnInfra.classList.toggle('hidden', !currentUser.can_access_infra);
            btnExec.classList.toggle('hidden', !currentUser.can_access_executive);
            btnAdmin.classList.toggle('hidden', currentUser.role !== 'admin');

            if (currentUser.can_access_executive) switchTab('executive');
            else if (currentUser.can_access_infra) switchTab('infra');
            else if (currentUser.role === 'admin') switchTab('admin_perm');

            refreshData();
        }

        async function handleLogout() {
            await fetch('/api/logout', {method: 'POST'});
            currentUser = null;
            document.getElementById('appView').classList.add('hidden');
            document.getElementById('loginView').classList.remove('hidden');
        }

        function switchTab(tab) {
            document.getElementById('viewExecutive').classList.toggle('hidden', tab !== 'executive');
            document.getElementById('viewInfra').classList.toggle('hidden', tab !== 'infra');
            document.getElementById('viewAdminPerm').classList.toggle('hidden', tab !== 'admin_perm');

            const btnExec = document.getElementById('tabExecutive');
            const btnInfra = document.getElementById('tabInfra');
            const btnAdmin = document.getElementById('tabAdmin');

            btnExec.className = tab === 'executive' ? 'px-4 py-2 rounded-lg text-white bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold' : 'px-4 py-2 rounded-lg text-slate-400 hover:text-white';
            btnInfra.className = tab === 'infra' ? 'px-4 py-2 rounded-lg text-white bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold' : 'px-4 py-2 rounded-lg text-slate-400 hover:text-white';
            btnAdmin.className = tab === 'admin_perm' ? 'px-4 py-2 rounded-lg text-white bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold' : 'px-4 py-2 rounded-lg text-slate-400 hover:text-white';

            if (tab === 'admin_perm') loadPermissionsTable();
        }

        async function refreshData() {
            fetchKPIs();
            fetchFinOps();
            fetchAudits();
        }

        async function fetchKPIs() {
            const res = await fetch('/api/kpis');
            const data = await res.json();
            document.getElementById('exec-audits').innerText = data.total_audits;
            document.getElementById('exec-score').innerText = data.avg_score;
            document.getElementById('exec-risks').innerText = data.high_risks;
            document.getElementById('infra-tokens').innerText = data.total_tokens.toLocaleString();
        }

        async function fetchFinOps() {
            const res = await fetch('/api/finops');
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
                    <td class="px-4 py-2 font-bold text-white">${p.monthly_calls.toLocaleString()} chamadas/mês</td>
                    <td class="px-4 py-2">${p.projected_input_tokens.toLocaleString()}</td>
                    <td class="px-4 py-2">${p.projected_output_tokens.toLocaleString()}</td>
                    <td class="px-4 py-2 text-purple-300">${p.projected_total_tokens.toLocaleString()}</td>
                    <td class="px-4 py-2 text-amber-300">US$ ${p.equivalent_cost_usd.toLocaleString()}</td>
                    <td class="px-4 py-2 text-emerald-400 font-bold">R$ ${p.equivalent_cost_brl.toLocaleString()}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function fetchAudits() {
            const res = await fetch('/api/audits');
            cachedAudits = await res.json();
            renderExecTable(cachedAudits);
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
                    <td class="px-6 py-4 font-mono text-xs text-amber-300">
                        <div>${a.protocol_number || 'PROT-309112'}</div>
                        <div class="text-[10px] text-slate-500">${a.filename}</div>
                    </td>
                    <td class="px-6 py-4 font-medium text-white">${a.operator_name || 'Operador'}</td>
                    <td class="px-6 py-4 text-slate-300">${a.client_name || 'Cliente Banco Engineer AI'}</td>
                    <td class="px-6 py-4"><span class="px-3 py-1 rounded-full text-xs font-bold ${scoreBadge}">${a.overall_score}</span></td>
                    <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-lg text-xs ${riskBadge}">${risk}</span></td>
                    <td class="px-6 py-4"><span class="text-xs px-2 py-1 rounded bg-slate-800 text-purple-300 border border-purple-500/30">${a.provider_used || 'Gemini'}</span></td>
                    <td class="px-6 py-4 text-right">
                        <button onclick='openModal(${JSON.stringify(a).replace(/'/g, "&apos;")})' class="text-xs bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 px-3.5 py-1.5 rounded-xl font-bold transition">
                            Inspecionar
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function openModal(audit) {
            const content = document.getElementById('modalContent');
            content.innerHTML = `
                <div class="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div>
                        <div class="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-md bg-amber-500/10 text-amber-400 text-[10px] font-bold border border-amber-500/20 mb-1">
                            <span>Auditoria de Atendimento • Banco Engineer AI</span>
                        </div>
                        <h2 class="text-xl font-extrabold text-white">${audit.filename}</h2>
                        <div class="text-xs text-slate-400 mt-0.5">Protocolo: <strong class="text-slate-200">${audit.protocol_number}</strong> • Operador: <strong class="text-slate-200">${audit.operator_name}</strong></div>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="bg-slate-900 p-4 rounded-2xl border border-slate-800 text-center">
                        <div class="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Score Final</div>
                        <div class="text-3xl font-extrabold text-emerald-400 mt-1">${audit.overall_score}</div>
                        <div class="text-[10px] text-slate-400">Scorecard de 0 a 100</div>
                    </div>

                    <div class="bg-slate-900 p-4 rounded-2xl border border-slate-800 text-center">
                        <div class="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Nível de Risco</div>
                        <div class="text-xl font-extrabold ${audit.risk_level === 'Baixo' ? 'text-emerald-400' : 'text-rose-400'} mt-1.5">${audit.risk_level || 'Baixo'}</div>
                    </div>

                    <div class="bg-slate-900 p-4 rounded-2xl border border-slate-800 text-center">
                        <div class="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Causa Raiz</div>
                        <div class="text-xs font-bold text-amber-300 mt-2">${audit.root_cause || 'Nao identificado'}</div>
                    </div>

                    <div class="bg-slate-900 p-4 rounded-2xl border border-slate-800 text-center">
                        <div class="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Resolutividade</div>
                        <div class="text-xs font-bold text-blue-400 mt-2">${audit.resolutivity || 'Resolvido'}</div>
                    </div>
                </div>

                <div class="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-2">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400">Resumo Executivo do Atendimento</h4>
                    <p class="text-sm text-slate-200 leading-relaxed">${audit.executive_summary}</p>
                </div>

                <div class="bg-slate-900 p-5 rounded-2xl border border-amber-500/20 space-y-2">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"></path></svg>
                        <span>Citação Literal da Evidência</span>
                    </h4>
                    <p class="text-xs italic text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono">"${audit.evidence_quote || 'Evidência confirmada durante o atendimento.'}"</p>
                </div>

                <div class="bg-slate-900 p-5 rounded-2xl border border-slate-800 space-y-2">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400">Justificativa Técnica da Nota</h4>
                    <p class="text-xs text-slate-300">${audit.score_justification}</p>
                </div>
            `;
            document.getElementById('auditModal').classList.remove('hidden');
        }

        function closeModal() {
            document.getElementById('auditModal').classList.add('hidden');
        }

        async function loadPermissionsTable() {
            const res = await fetch('/api/admin/permissions');
            if (!res.ok) return;
            const users = await res.json();
            const tbody = document.getElementById('permTableBody');
            tbody.innerHTML = '';

            users.forEach(u => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="px-6 py-4 font-bold text-white">${u.name} <span class="text-xs text-slate-500">(${u.username})</span></td>
                    <td class="px-6 py-4"><span class="px-2.5 py-0.5 rounded text-xs font-bold ${u.role === 'admin' ? 'bg-amber-500/20 text-amber-400' : 'bg-blue-500/20 text-blue-400'}">${u.role.toUpperCase()}</span></td>
                    <td class="px-6 py-4 text-center">
                        <input type="checkbox" id="perm_infra_${u.username}" ${u.can_access_infra ? 'checked' : ''} ${u.username === 'admin' ? 'disabled' : ''} class="w-4 h-4 rounded text-amber-500">
                    </td>
                    <td class="px-6 py-4 text-center">
                        <input type="checkbox" id="perm_exec_${u.username}" ${u.can_access_executive ? 'checked' : ''} class="w-4 h-4 rounded text-amber-500">
                    </td>
                    <td class="px-6 py-4 text-right">
                        <button onclick="saveUserPermission('${u.username}')" class="text-xs bg-amber-500 hover:bg-amber-400 text-slate-950 px-3 py-1.5 rounded-xl font-bold transition">
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

            const res = await fetch('/api/admin/permissions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: username, can_access_infra: inf, can_access_executive: exc})
            });
            if (res.ok) alert(`Permissões atualizadas com sucesso para o usuário '${username}'!`);
        }

        // Auto check session on load
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
    username = data.get("username", "")
    password = data.get("password", "")
    user = db.authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos. Tente 'admin'/'admin1' ou 'usuario'/'usuario1'.")
    
    session_id = os.urandom(16).hex()
    SESSIONS[session_id] = user
    response.set_cookie(key="auditai_session", value=session_id, httponly=True)
    return {"status": "ok", "user": user}

@app.post("/api/logout")
def logout_api(response: Response, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    response.delete_cookie("auditai_session")
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
    return db.get_all_audits(limit=309)

@app.get("/api/audit/{audit_id}")
def get_single_audit(audit_id: int):
    audits = db.get_all_audits(limit=500)
    for a in audits:
        if a["id"] == audit_id:
            return a
    raise HTTPException(status_code=404, detail="Audit not found")
