import os
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("TrafficController.Database")

class AuditDatabase:
    """
    SQLite Repository Manager (Python First -> Database -> LLM Last).
    Gerencia persistência relacional normalizada pré-LLM e pós-LLM em
    C:\\Users\\fferr\\Desktop\\projetoRATE\\repositoy\\audit_database.db.
    """
    def __init__(self, db_path: str = r"C:\Users\fferr\Desktop\projetoRATE\repositoy\audit_database.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # --- TABELAS NOVAS DA ARQUITETURA PYTHON FIRST ---
            # 1. Atendimentos (Ingestão & Metadados)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS atendimentos (
                atendimento_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                status TEXT DEFAULT 'RECEIVED',
                lote TEXT DEFAULT 'DEFAULT',
                ingestion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 2. Transcrições (Original e Normalizada)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcricoes (
                atendimento_id TEXT PRIMARY KEY,
                transcricao_original TEXT NOT NULL,
                transcricao_normalizada TEXT NOT NULL,
                FOREIGN KEY (atendimento_id) REFERENCES atendimentos(atendimento_id) ON DELETE CASCADE
            )
            """)

            # 3. Evidências (Indexador de Evidências com rastreabilidade por linha e speaker)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidencias (
                evidence_id TEXT PRIMARY KEY,
                atendimento_id TEXT NOT NULL,
                tipo TEXT NOT NULL,
                valor TEXT NOT NULL,
                speaker TEXT,
                linha_inicio INTEGER,
                linha_fim INTEGER,
                trecho TEXT,
                metodo_extracao TEXT,
                confianca REAL,
                FOREIGN KEY (atendimento_id) REFERENCES atendimentos(atendimento_id) ON DELETE CASCADE
            )
            """)

            # 4. Data Quality (Validações de integridade)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_quality (
                atendimento_id TEXT PRIMARY KEY,
                score INTEGER NOT NULL,
                flags_json TEXT,
                word_count INTEGER,
                line_count INTEGER,
                FOREIGN KEY (atendimento_id) REFERENCES atendimentos(atendimento_id) ON DELETE CASCADE
            )
            """)

            # 5. LLM Jobs (Fila persistente e idempotente)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_jobs (
                job_id TEXT PRIMARY KEY,
                atendimento_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                contract_version TEXT DEFAULT 'v1.0',
                status TEXT DEFAULT 'READY_FOR_LLM',
                estimated_input_tokens INTEGER,
                payload_json TEXT,
                attempt INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (atendimento_id) REFERENCES atendimentos(atendimento_id) ON DELETE CASCADE
            )
            """)

            # 6. LLM Resultados & Economia de Tokens
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_resultados (
                job_id TEXT PRIMARY KEY,
                atendimento_id TEXT NOT NULL,
                tokens_raw INTEGER,
                tokens_sent INTEGER,
                tokens_saved INTEGER,
                compression_ratio REAL,
                json_resposta TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES llm_jobs(job_id) ON DELETE CASCADE
            )
            """)

            # 7. LLM Pricing Table (Preços Comerciais Versionados)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_pricing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                pricing_type TEXT DEFAULT 'PER_MILLION_TOKENS',
                currency TEXT DEFAULT 'USD',
                input_price_per_million REAL NOT NULL,
                output_price_per_million REAL NOT NULL,
                cached_input_price_per_million REAL DEFAULT 0.0,
                reasoning_price_per_million REAL DEFAULT 0.0,
                pricing_version TEXT DEFAULT 'v2026.09.05',
                source TEXT DEFAULT 'Official Commercial Pricing Table',
                effective_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 8. FX Rates (Cotações de Câmbio USD -> BRL)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fx_rate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                currency_from TEXT DEFAULT 'USD',
                currency_to TEXT DEFAULT 'BRL',
                rate REAL NOT NULL,
                reference_date TEXT NOT NULL,
                source TEXT DEFAULT 'Banco Central do Brasil / Comercial',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Populate initial FX Rate if empty
            cursor.execute("SELECT COUNT(*) FROM fx_rate")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                INSERT INTO fx_rate (currency_from, currency_to, rate, reference_date, source)
                VALUES ('USD', 'BRL', 5.1262, '2026-09-05', 'Banco Central do Brasil / Comercial')
                """)

            # 9. LLM Usage Registro Individual FinOps
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_usage (
                usage_id TEXT PRIMARY KEY,
                atendimento_id TEXT NOT NULL,
                job_id TEXT,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cached_tokens INTEGER DEFAULT 0,
                reasoning_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER NOT NULL,
                actual_cost_usd REAL DEFAULT 0.0,
                equivalent_cost_usd REAL NOT NULL,
                savings_usd REAL NOT NULL,
                usd_brl_rate REAL NOT NULL,
                actual_cost_brl REAL DEFAULT 0.0,
                equivalent_cost_brl REAL NOT NULL,
                savings_brl REAL NOT NULL,
                pricing_version TEXT DEFAULT 'v2026.09.05',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # --- TABELAS LEGADAS (RETROCOMPATIBILIDADE 100%) ---
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                protocol_number TEXT,
                operator_name TEXT,
                client_name TEXT,
                executive_summary TEXT,
                call_classification TEXT,
                overall_score REAL,
                score_justification TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS scorecards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id INTEGER NOT NULL,
                cx_score INTEGER,
                operator_quality_score INTEGER,
                technical_score INTEGER,
                behavioral_score INTEGER,
                resolutivity TEXT,
                FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id INTEGER NOT NULL,
                risk_level TEXT,
                identified_risks TEXT,
                root_cause TEXT,
                problem_owner TEXT,
                evidence_quote TEXT,
                FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id INTEGER NOT NULL,
                operator_opportunities TEXT,
                operational_opportunities TEXT,
                FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id INTEGER,
                provider_used TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                latency_sec REAL,
                masked_pii_count INTEGER,
                status_code INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE SET NULL
            )
            """)
            # 10. Users & Permissions (RBAC)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_permissions (
                username TEXT PRIMARY KEY,
                can_access_infra INTEGER DEFAULT 1,
                can_access_executive INTEGER DEFAULT 1,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
            )
            """)

            # Seed default users if empty
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                INSERT INTO users (username, password, role, name)
                VALUES 
                    ('admin', 'admin1', 'admin', 'Administrador do Sistema'),
                    ('usuario', 'usuario1', 'usuario', 'Auditor de Qualidade')
                """)
                cursor.execute("""
                INSERT INTO user_permissions (username, can_access_infra, can_access_executive)
                VALUES 
                    ('admin', 1, 1),
                    ('usuario', 0, 1)
                """)

            conn.commit()
            logger.info(f"[Database] SQLite database initialized at {self.db_path}")
        finally:
            conn.close()

    def save_python_preprocessing(
        self,
        atendimento_id: str,
        filename: str,
        file_hash: str,
        raw_text: str,
        norm_text: str,
        evidences: List[Any],
        data_quality: Dict[str, Any],
        lote: str = "DEFAULT"
    ):
        """Salva a fase Python no SQLite antes de qualquer chamada à LLM."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            # 1. Atendimento
            cursor.execute("""
                INSERT OR REPLACE INTO atendimentos (atendimento_id, filename, file_hash, status, lote)
                VALUES (?, ?, ?, 'PREPROCESSED', ?)
            """, (atendimento_id, filename, file_hash, lote))

            # 2. Transcrição
            cursor.execute("""
                INSERT OR REPLACE INTO transcricoes (atendimento_id, transcricao_original, transcricao_normalizada)
                VALUES (?, ?, ?)
            """, (atendimento_id, raw_text, norm_text))

            # 3. Data Quality
            cursor.execute("""
                INSERT OR REPLACE INTO data_quality (atendimento_id, score, flags_json, word_count, line_count)
                VALUES (?, ?, ?, ?, ?)
            """, (
                atendimento_id,
                data_quality.get("score", 100),
                json.dumps(data_quality.get("flags", []), ensure_ascii=False),
                data_quality.get("word_count", 0),
                data_quality.get("line_count", 0)
            ))

            # 4. Evidências
            for ev in evidences:
                ev_dict = ev if isinstance(ev, dict) else ev.__dict__
                cursor.execute("""
                    INSERT OR REPLACE INTO evidencias (
                        evidence_id, atendimento_id, tipo, valor, speaker,
                        linha_inicio, linha_fim, trecho, metodo_extracao, confianca
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ev_dict["evidence_id"], atendimento_id, ev_dict["tipo"], ev_dict["valor"],
                    ev_dict.get("speaker", "DESCONHECIDO"), ev_dict.get("linha_inicio", 1),
                    ev_dict.get("linha_fim", 1), ev_dict.get("trecho", ""),
                    ev_dict.get("metodo_extracao", "REGEX"), ev_dict.get("confianca", 0.9)
                ))

            conn.commit()
        finally:
            conn.close()

    def save_llm_usage(self, usage_res: Any, job_id: str = None) -> str:
        """Salva o registro individual FinOps de cada chamada na tabela llm_usage."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            u_dict = usage_res if isinstance(usage_res, dict) else usage_res.__dict__
            usage_id = f"USG_{u_dict['atendimento_id']}_{u_dict['provider']}"
            cursor.execute("""
                INSERT OR REPLACE INTO llm_usage (
                    usage_id, atendimento_id, job_id, provider, model,
                    input_tokens, output_tokens, cached_tokens, reasoning_tokens, total_tokens,
                    actual_cost_usd, equivalent_cost_usd, savings_usd,
                    usd_brl_rate, actual_cost_brl, equivalent_cost_brl, savings_brl,
                    pricing_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usage_id, u_dict["atendimento_id"], job_id, u_dict["provider"], u_dict["model"],
                u_dict["input_tokens"], u_dict["output_tokens"], u_dict.get("cached_tokens", 0), u_dict.get("reasoning_tokens", 0), u_dict["total_tokens"],
                u_dict["actual_cost_usd"], u_dict["equivalent_cost_usd"], u_dict["savings_usd"],
                u_dict["usd_brl_rate"], u_dict["actual_cost_brl"], u_dict["equivalent_cost_brl"], u_dict["savings_brl"],
                u_dict["pricing_version"]
            ))
            conn.commit()
            return usage_id
        finally:
            conn.close()

    def get_finops_summary(self) -> Dict[str, Any]:
        """Calcula totais consolidados e indicadores FinOps para o Web Dashboard."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT atendimento_id) as total_calls,
                    SUM(input_tokens) as total_input,
                    SUM(output_tokens) as total_output,
                    SUM(cached_tokens) as total_cached,
                    SUM(total_tokens) as total_tokens,
                    SUM(actual_cost_brl) as actual_brl,
                    SUM(equivalent_cost_brl) as equivalent_brl,
                    SUM(savings_brl) as savings_brl,
                    AVG(usd_brl_rate) as avg_rate
                FROM llm_usage
            """)
            row = cursor.fetchone()
            total_calls = row["total_calls"] or 0
            total_input = row["total_input"] or 0
            total_output = row["total_output"] or 0
            total_cached = row["total_cached"] or 0
            total_tokens = row["total_tokens"] or 0
            actual_brl = row["actual_brl"] or 0.0
            equivalent_brl = row["equivalent_brl"] or 0.0
            savings_brl = row["savings_brl"] or 0.0
            avg_rate = row["avg_rate"] or 5.1262

            cost_per_call = (equivalent_brl / total_calls) if total_calls > 0 else 0.0
            avg_input_per_call = (total_input / total_calls) if total_calls > 0 else 0
            avg_output_per_call = (total_output / total_calls) if total_calls > 0 else 0

            return {
                "total_calls": total_calls,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_cached_tokens": total_cached,
                "total_tokens": total_tokens,
                "actual_cost_brl": round(actual_brl, 2),
                "equivalent_cost_brl": round(equivalent_brl, 2),
                "savings_brl": round(savings_brl, 2),
                "cost_per_call_brl": round(cost_per_call, 4),
                "avg_input_per_call": int(avg_input_per_call),
                "avg_output_per_call": int(avg_output_per_call),
                "usd_brl_rate": round(avg_rate, 4),
                "exchange_rate_date": "05/09/2026",
                "exchange_rate_source": "Banco Central do Brasil / Comercial"
            }
        finally:
            conn.close()

    def save_audit(self, task_id: str, filename: str, audit_data: Dict[str, Any], telemetry_data: Dict[str, Any]) -> int:
        """Saves a complete audit record with relational scorecards, risks, opportunities, and telemetry."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Insert main audit
            cursor.execute("""
            INSERT OR REPLACE INTO audits (
                task_id, filename, protocol_number, operator_name, client_name,
                executive_summary, call_classification, overall_score, score_justification
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                filename,
                audit_data.get("numero_protocolo", "Nao identificado"),
                audit_data.get("nome_operador", "Operador"),
                audit_data.get("nome_cliente", "Cliente"),
                audit_data.get("resumo_executivo", ""),
                audit_data.get("classificacao_atendimento", "Geral"),
                audit_data.get("score_final", 85.0),
                audit_data.get("justificativa_score", "")
            ))

            audit_id = cursor.lastrowid

            # Insert scorecard
            scorecard = audit_data.get("scorecard", {})
            cursor.execute("""
            INSERT INTO scorecards (
                audit_id, cx_score, operator_quality_score, technical_score, behavioral_score, resolutivity
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                audit_id,
                scorecard.get("pontuacao_cx", 80),
                scorecard.get("pontuacao_qualidade_operador", 80),
                scorecard.get("pontuacao_tecnica", 80),
                scorecard.get("pontuacao_comportamental", 80),
                scorecard.get("resolutivity", "Resolvido")
            ))

            # Insert risk analysis
            risk = audit_data.get("risco_e_causa_raiz", {})
            cursor.execute("""
            INSERT INTO risk_analyses (
                audit_id, risk_level, identified_risks, root_cause, problem_owner, evidence_quote
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                audit_id,
                risk.get("nivel_risco", "Baixo"),
                json.dumps(risk.get("riscos_identificados", []), ensure_ascii=False),
                risk.get("causa_raiz", "Nao identificado"),
                risk.get("responsavel_problema", "Nao identificado"),
                risk.get("citacao_evidencia", "")
            ))

            # Insert opportunities
            opp = audit_data.get("oportunidades", {})
            cursor.execute("""
            INSERT INTO opportunities (
                audit_id, operator_opportunities, operational_opportunities
            ) VALUES (?, ?, ?)
            """, (
                audit_id,
                json.dumps(opp.get("oportunidades_operador", []), ensure_ascii=False),
                json.dumps(opp.get("oportunidades_operacionais", []), ensure_ascii=False)
            ))

            # Insert telemetry
            cursor.execute("""
            INSERT INTO telemetry_logs (
                audit_id, provider_used, input_tokens, output_tokens, latency_sec, masked_pii_count, status_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_id,
                telemetry_data.get("provider_used", "Groq"),
                telemetry_data.get("input_tokens", 0),
                telemetry_data.get("output_tokens", 0),
                telemetry_data.get("latency_sec", 0.0),
                telemetry_data.get("masked_pii_count", 0),
                telemetry_data.get("status_code", 200)
            ))

            conn.commit()
            return audit_id
        finally:
            conn.close()

    def get_all_audits(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Returns all completed audit records joined with scorecards and risk analyses."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            query = """
            SELECT 
                a.id, a.task_id, a.filename, a.protocol_number, a.operator_name, a.client_name,
                a.executive_summary, a.call_classification, a.overall_score, a.score_justification, a.created_at,
                s.cx_score, s.operator_quality_score, s.technical_score, s.behavioral_score, s.resolutivity,
                r.risk_level, r.identified_risks, r.root_cause, r.problem_owner, r.evidence_quote,
                t.provider_used, t.input_tokens, t.output_tokens, t.latency_sec, t.masked_pii_count,
                tr.transcricao_original
            FROM audits a
            LEFT JOIN scorecards s ON a.id = s.audit_id
            LEFT JOIN risk_analyses r ON a.id = r.audit_id
            LEFT JOIN telemetry_logs t ON a.id = t.audit_id
            LEFT JOIN atendimentos at ON at.filename = a.filename
            LEFT JOIN transcricoes tr ON tr.atendimento_id = at.atendimento_id
            ORDER BY a.id DESC
            LIMIT ?
            """
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item.get("identified_risks"):
                    try:
                        item["identified_risks"] = json.loads(item["identified_risks"])
                    except Exception:
                        pass
                results.append(item)
            return results
        finally:
            conn.close()

    def get_token_savings_summary(self) -> Dict[str, Any]:
        """Retorna estatísticas acumuladas de economia de tokens pela arquitetura Python First."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(tokens_raw), SUM(tokens_sent), SUM(tokens_saved), AVG(compression_ratio) FROM llm_resultados")
            row = cursor.fetchone()
            if row and row[0]:
                return {
                    "total_raw_tokens": row[0],
                    "total_sent_tokens": row[1],
                    "total_saved_tokens": row[2],
                    "avg_compression_ratio": round(row[3] or 0.0, 2)
                }
            return {"total_raw_tokens": 0, "total_sent_tokens": 0, "total_saved_tokens": 0, "avg_compression_ratio": 1.0}
        finally:
            conn.close()

    def get_kpi_summary(self) -> Dict[str, Any]:
        """Calculates global executive KPI statistics for the web dashboard."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM audits")
            total_audits = cursor.fetchone()[0] or 0

            cursor.execute("SELECT AVG(overall_score) FROM audits")
            avg_score = cursor.fetchone()[0] or 0.0

            cursor.execute("SELECT COUNT(*) FROM risk_analyses WHERE risk_level IN ('Alto', 'Critico')")
            high_risks = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(input_tokens + output_tokens) FROM telemetry_logs")
            total_tokens = cursor.fetchone()[0] or 0

            return {
                "total_audits": total_audits,
                "avg_score": round(avg_score, 1),
                "high_risks": high_risks,
                "total_tokens": total_tokens
            }
        finally:
            conn.close()

    def authenticate_user(self, username_or_email: str, password_input: str) -> Optional[Dict[str, Any]]:
        """Autentica usuário e retorna dados com permissões."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            u_clean = username_or_email.strip().lower().replace("@engineer.ai", "")
            cursor.execute("""
                SELECT u.username, u.role, u.name, p.can_access_infra, p.can_access_executive
                FROM users u
                LEFT JOIN user_permissions p ON u.username = p.username
                WHERE (u.username = ? OR u.username = ?) AND u.password = ?
            """, (username_or_email.strip().lower(), u_clean, password_input.strip()))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res["can_access_infra"] = bool(res.get("can_access_infra", 1 if res["role"] == "admin" else 0))
                res["can_access_executive"] = bool(res.get("can_access_executive", 1))
                return res
            return None
        finally:
            conn.close()

    def get_all_users_permissions(self) -> List[Dict[str, Any]]:
        """Retorna lista de todos os usuários com suas permissões para o Admin."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.username, u.role, u.name, 
                       COALESCE(p.can_access_infra, 1) as can_access_infra,
                       COALESCE(p.can_access_executive, 1) as can_access_executive
                FROM users u
                LEFT JOIN user_permissions p ON u.username = p.username
                ORDER BY u.role ASC, u.username ASC
            """)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["can_access_infra"] = bool(item["can_access_infra"])
                item["can_access_executive"] = bool(item["can_access_executive"])
                results.append(item)
            return results
        finally:
            conn.close()

    def get_operators_summary(self) -> List[Dict[str, Any]]:
        """Retorna estatísticas consolidadas por operador para a aba Operadores do LMS."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    a.operator_name,
                    COUNT(*) as total_calls,
                    ROUND(AVG(a.overall_score), 1) as avg_score,
                    SUM(CASE WHEN r.risk_level IN ('Alto', 'Crítico') THEN 1 ELSE 0 END) as high_risks
                FROM audits a
                LEFT JOIN risk_analyses r ON a.id = r.audit_id
                GROUP BY a.operator_name
                ORDER BY avg_score DESC
            """)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                score = item["avg_score"] or 0
                if score >= 88: item["performance_status"] = "Top Performer"
                elif score >= 75: item["performance_status"] = "Regular"
                else: item["performance_status"] = "Necessita Revisão"
                results.append(item)
            return results
        finally:
            conn.close()

    def update_user_permissions(self, username: str, can_access_infra: bool, can_access_executive: bool) -> bool:
        """Atualiza permissões de visualização para um usuário."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_permissions (username, can_access_infra, can_access_executive)
                VALUES (?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    can_access_infra = excluded.can_access_infra,
                    can_access_executive = excluded.can_access_executive
            """, (username, 1 if can_access_infra else 0, 1 if can_access_executive else 0))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Could not update permissions for {username}: {e}")
            return False
        finally:
            conn.close()

    def create_session(self, session_id: str, username: str) -> bool:
        """Salva uma sessão ativa no SQLite para persistência total."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO user_sessions (session_id, username) VALUES (?, ?)", (session_id, username))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")
            return False
        finally:
            conn.close()

    def get_user_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Recupera usuário autenticado por ID de sessão mantido no SQLite."""
        if not session_id:
            return None
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.username, u.role, u.name,
                       COALESCE(p.can_access_infra, 1) as can_access_infra,
                       COALESCE(p.can_access_executive, 1) as can_access_executive
                FROM user_sessions s
                JOIN users u ON s.username = u.username
                LEFT JOIN user_permissions p ON u.username = p.username
                WHERE s.session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res["can_access_infra"] = bool(res.get("can_access_infra", 1 if res["role"] == "admin" else 0))
                res["can_access_executive"] = bool(res.get("can_access_executive", 1))
                return res
            return None
        finally:
            conn.close()

    def delete_session(self, session_id: str) -> bool:
        """Remove sessão ativa ao fazer logout."""
        if not session_id:
            return True
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return True
        finally:
            conn.close()

