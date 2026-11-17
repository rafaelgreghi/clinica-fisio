import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import database as db

# ====================== CONFIGURAÇÃO DA PÁGINA ======================
st.set_page_config(
    page_title="Sistema Clínica de Fisioterapia",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa o banco
db.init_db()

# ====================== FUNÇÕES AUXILIARES ======================

def check_login():
    if "user" not in st.session_state:
        st.session_state.user = None
    return st.session_state.user is not None

def logout():
    st.session_state.user = None
    st.rerun()

def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ====================== TELA DE LOGIN ======================

def login_page():
    st.title("🏥 Sistema de Clínica de Fisioterapia")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Acesso ao Sistema")
        
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit:
                user = db.authenticate_user(username, password)
                if user:
                    st.session_state.user = user
                    st.success(f"Bem-vindo(a), {user['name']}!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos")
        
        st.info("**Acesso inicial:** usuário `admin` | senha `admin123`")
        st.caption("Altere a senha do administrador após o primeiro acesso.")

# ====================== SIDEBAR ======================

def sidebar():
    user = st.session_state.user
    
    st.sidebar.title("🏥 Clínica Fisio")
    st.sidebar.markdown(f"**Usuário:** {user['name']}")
    st.sidebar.markdown(f"**Perfil:** {'Administrador' if user['role'] == 'admin' else 'Profissional'}")
    st.sidebar.markdown("---")
    
    menu_options = ["🏠 Início"]
    
    if user["role"] == "admin":
        menu_options.extend([
            "👥 Pacientes Ativos",
            "📂 Pacientes Inativos (Histórico)",
            "📅 Agenda Geral",
            "💰 Controle Financeiro",
            "👨‍⚕️ Profissionais",
            "📊 Relatórios"
        ])
    else:
        menu_options.extend([
            "👥 Meus Pacientes Ativos",
            "📂 Meus Pacientes Inativos",
            "📅 Minha Agenda",
            "📝 Evoluções",
            "💰 Meus Atendimentos / Financeiro"
        ])
    
    menu_options.append("🚪 Sair")
    
    choice = st.sidebar.radio("Menu", menu_options, label_visibility="collapsed")
    
    if choice == "🚪 Sair":
        logout()
    
    return choice

# ====================== PÁGINAS ======================

def page_home():
    user = st.session_state.user
    st.title(f"Olá, {user['name']} 👋")
    st.markdown("---")
    
    today = date.today().isoformat()
    
    col1, col2, col3, col4 = st.columns(4)
    
    if user["role"] == "admin":
        patients_ativos = db.get_patients(status="ativo")
        patients_inativos = db.get_patients(status="inativo")
        appointments_today = db.get_appointments(date_from=today, date_to=today)
        summary = db.get_financial_summary(
            date_from=date.today().replace(day=1).isoformat(),
            date_to=today
        )
        
        with col1:
            st.metric("Pacientes Ativos", len(patients_ativos))
        with col2:
            st.metric("Pacientes Inativos", len(patients_inativos))
        with col3:
            st.metric("Agendamentos Hoje", len(appointments_today))
        with col4:
            st.metric("Receita do Mês", format_currency(summary["geral"]["total_pago"]))
        
        st.markdown("### 📅 Agendamentos de Hoje")
        if appointments_today:
            df = pd.DataFrame(appointments_today)
            df_display = df[["start_time", "patient_name", "professional_name", "appointment_type", "status", "value"]]
            df_display.columns = ["Horário", "Paciente", "Profissional", "Tipo", "Status", "Valor"]
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum agendamento para hoje.")
    
    else:
        my_appointments = db.get_appointments(professional_id=user["id"], date_from=today, date_to=today)
        my_patients = db.get_patients(status="ativo")
        
        with col1:
            st.metric("Meus Agendamentos Hoje", len(my_appointments))
        with col2:
            st.metric("Pacientes Ativos na Clínica", len(my_patients))
        
        st.markdown("### 📅 Minha Agenda de Hoje")
        if my_appointments:
            df = pd.DataFrame(my_appointments)
            df_display = df[["start_time", "patient_name", "appointment_type", "status", "value"]]
            df_display.columns = ["Horário", "Paciente", "Tipo", "Status", "Valor"]
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("Você não tem agendamentos para hoje.")


def page_patients(status="ativo", only_mine=False):
    user = st.session_state.user
    title = "Pacientes Ativos" if status == "ativo" else "Pacientes Inativos (Histórico)"
    if only_mine:
        title = "Meus " + title
    
    st.title(f"👥 {title}")
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Buscar por nome, CPF ou telefone", key=f"search_{status}")
    with col2:
        st.write("")
        st.write("")
        if st.button("➕ Novo Paciente", use_container_width=True):
            st.session_state.show_new_patient = True
    
    if st.session_state.get("show_new_patient", False):
        with st.expander("Cadastrar Novo Paciente", expanded=True):
            with st.form("new_patient_form"):
                c1, c2 = st.columns(2)
                with c1:
                    full_name = st.text_input("Nome Completo *")
                    cpf = st.text_input("CPF")
                    birth_date = st.date_input("Data de Nascimento", value=None)
                    phone = st.text_input("Telefone")
                with c2:
                    email = st.text_input("E-mail")
                    address = st.text_input("Endereço")
                    health_insurance = st.selectbox("Convênio", ["Particular", "Unimed", "Bradesco Saúde", "Amil", "SulAmérica", "Outro"])
                    notes = st.text_area("Observações")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submitted = st.form_submit_button("Salvar Paciente", use_container_width=True)
                with col_btn2:
                    cancel = st.form_submit_button("Cancelar", use_container_width=True)
                
                if cancel:
                    st.session_state.show_new_patient = False
                    st.rerun()
                
                if submitted:
                    if not full_name:
                        st.error("Nome é obrigatório")
                    else:
                        data = {
                            "full_name": full_name,
                            "cpf": cpf,
                            "birth_date": birth_date.isoformat() if birth_date else None,
                            "phone": phone,
                            "email": email,
                            "address": address,
                            "health_insurance": health_insurance,
                            "status": "ativo",
                            "notes": notes
                        }
                        db.create_patient(data, user["id"])
                        st.success("Paciente cadastrado com sucesso!")
                        st.session_state.show_new_patient = False
                        st.rerun()
    
    patients = db.get_patients(status=status, search=search if search else None)
    
    if not patients:
        st.info("Nenhum paciente encontrado.")
        return
    
    st.markdown(f"**Total:** {len(patients)} paciente(s)")
    
    for p in patients:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            with col1:
                st.markdown(f"**{p['full_name']}**")
                st.caption(f"CPF: {p['cpf'] or '-'} | Tel: {p['phone'] or '-'}")
            with col2:
                st.markdown(f"Convênio: **{p['health_insurance']}**")
            with col3:
                if p['status'] == 'ativo':
                    st.success("Ativo")
                else:
                    st.warning("Inativo")
            with col4:
                if st.button("Ver / Editar", key=f"view_{p['id']}"):
                    st.session_state.selected_patient = p['id']
                    st.session_state.page_mode = "patient_detail"
                    st.rerun()
            
            st.markdown("---")


def page_patient_detail():
    patient_id = st.session_state.get("selected_patient")
    if not patient_id:
        st.warning("Nenhum paciente selecionado")
        return
    
    patient = db.get_patient_by_id(patient_id)
    if not patient:
        st.error("Paciente não encontrado")
        return
    
    st.title(f"👤 {patient['full_name']}")
    
    if st.button("← Voltar"):
        st.session_state.selected_patient = None
        st.session_state.page_mode = None
        st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Dados Pessoais")
        st.write(f"**CPF:** {patient['cpf'] or '-'}")
        st.write(f"**Nascimento:** {patient['birth_date'] or '-'}")
        st.write(f"**Telefone:** {patient['phone'] or '-'}")
        st.write(f"**E-mail:** {patient['email'] or '-'}")
    with col2:
        st.markdown("### Informações Clínicas")
        st.write(f"**Convênio:** {patient['health_insurance']}")
        st.write(f"**Status:** {patient['status'].capitalize()}")
        st.write(f"**Endereço:** {patient['address'] or '-'}")
        st.write(f"**Observações:** {patient['notes'] or '-'}")
    
    st.markdown("### Ações")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if patient['status'] == 'ativo':
            if st.button("Arquivar (Tornar Inativo)", use_container_width=True):
                db.update_patient_status(patient_id, "inativo")
                st.success("Paciente arquivado")
                st.rerun()
        else:
            if st.button("Reativar Paciente", use_container_width=True):
                db.update_patient_status(patient_id, "ativo")
                st.success("Paciente reativado")
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 📝 Histórico de Evoluções")
    
    evolutions = db.get_evolutions_by_patient(patient_id)
    if evolutions:
        for evo in evolutions:
            with st.expander(f"{evo['session_date']} — {evo['professional_name']}"):
                st.write(f"**Queixa:** {evo['complaint'] or '-'}")
                st.write(f"**Avaliação:** {evo['assessment'] or '-'}")
                st.write(f"**Conduta:** {evo['conduct'] or '-'}")
                st.write(f"**Evolução:** {evo['evolution'] or '-'}")
    else:
        st.info("Nenhuma evolução registrada ainda.")
    
    st.markdown("### ➕ Registrar Nova Evolução")
    with st.form("new_evolution"):
        session_date = st.date_input("Data da Sessão", value=date.today())
        complaint = st.text_area("Queixa Principal")
        assessment = st.text_area("Avaliação")
        conduct = st.text_area("Conduta")
        evolution = st.text_area("Evolução / Observações")
        
        if st.form_submit_button("Salvar Evolução"):
            data = {
                "patient_id": patient_id,
                "professional_id": st.session_state.user["id"],
                "session_date": session_date.isoformat(),
                "complaint": complaint,
                "assessment": assessment,
                "conduct": conduct,
                "evolution": evolution
            }
            db.create_evolution(data)
            st.success("Evolução salva com sucesso!")
            st.rerun()

def page_agenda(professional_id=None):
    user = st.session_state.user
    is_admin = user["role"] == "admin"
    
    st.title("📅 Agenda Geral" if is_admin else "📅 Minha Agenda")
    st.markdown("---")
    
    # ====================== FILTROS ======================
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        # Semana de referência
        hoje = date.today()
        inicio_semana = hoje - timedelta(days=hoje.weekday())  # Segunda-feira
        data_inicio = st.date_input("Semana a partir de", value=inicio_semana)
    
    with col2:
        if is_admin:
            professionals = db.get_all_professionals()
            if not professionals:
                st.warning("Nenhum profissional cadastrado.")
                return
            prof_options = {p["name"]: p["id"] for p in professionals}
            selected_prof_name = st.selectbox("Selecionar Profissional", list(prof_options.keys()))
            professional_id = prof_options[selected_prof_name]
        else:
            professional_id = user["id"]
            selected_prof_name = user["name"]
    
    with col3:
        st.write("")
        st.write("")
        if st.button("➕ Novo Agendamento", use_container_width=True):
            st.session_state.show_new_appointment = True
    
    # Calcula os 7 dias da semana
    dias_semana = []
    for i in range(7):
        dia = data_inicio + timedelta(days=i)
        dias_semana.append(dia)
    
    nomes_dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    
    # Busca os agendamentos da semana do profissional
    appointments = db.get_appointments(
        professional_id=professional_id,
        date_from=dias_semana[0].isoformat(),
        date_to=dias_semana[6].isoformat()
    )
    
    # Organiza os agendamentos por data e horário
    agenda_dict = {}
    for appt in appointments:
        data = appt["appointment_date"]
        hora = appt["start_time"]
        if data not in agenda_dict:
            agenda_dict[data] = {}
        agenda_dict[data][hora] = appt
    
    # ====================== CALENDÁRIO SEMANAL ======================
    st.markdown(f"### Agenda de **{selected_prof_name}**")
    st.caption(f"Semana de {dias_semana[0].strftime('%d/%m/%Y')} a {dias_semana[6].strftime('%d/%m/%Y')}")
    
    # Horários do dia (de 07:00 às 20:00 de 30 em 30 minutos)
    horarios = []
    for h in range(7, 21):
        horarios.append(f"{h:02d}:00")
        if h < 20:
            horarios.append(f"{h:02d}:30")
    
    # Cria a tabela do calendário
    dados_calendario = []
    
    for horario in horarios:
        linha = {"Horário": horario}
        for i, dia in enumerate(dias_semana):
            data_str = dia.isoformat()
            nome_dia = nomes_dias[i]
            chave_coluna = f"{nome_dia}\n{dia.strftime('%d/%m')}"
            
            if data_str in agenda_dict and horario in agenda_dict[data_str]:
                appt = agenda_dict[data_str][horario]
                paciente = appt["patient_name"]
                tipo = appt.get("appointment_type", "")
                status = appt.get("status", "")
                
                # Formata o texto da célula
                texto = f"{paciente}"
                if tipo:
                    texto += f"\n({tipo})"
                if status in ["faltou", "cancelado"]:
                    texto += f"\n[{status}]"
                
                linha[chave_coluna] = texto
            else:
                linha[chave_coluna] = ""
        
        dados_calendario.append(linha)
    
    df_calendario = pd.DataFrame(dados_calendario)
    
    # Mostra o calendário
    st.dataframe(
        df_calendario,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # ====================== FORMULÁRIO NOVO AGENDAMENTO ======================
    if st.session_state.get("show_new_appointment", False):
        with st.expander("Novo Agendamento", expanded=True):
            patients = db.get_patients(status="ativo")
            patient_options = {f"{p['full_name']}": p['id'] for p in patients}
            
            with st.form("new_appointment_form"):
                c1, c2 = st.columns(2)
                with c1:
                    selected_patient = st.selectbox("Paciente *", list(patient_options.keys()) if patient_options else ["Nenhum paciente ativo"])
                    appt_date = st.date_input("Data *", value=date.today())
                    start_time = st.time_input("Horário de Início *")
                with c2:
                    if is_admin:
                        selected_prof = selected_prof_name
                    else:
                        selected_prof = user["name"]
                    
                    appt_type = st.selectbox("Tipo", ["Avaliação", "Sessão", "Retorno", "Pilates", "RPG", "Outro"])
                    value = st.number_input("Valor (R$)", min_value=0.0, step=10.0, value=0.0)
                    notes = st.text_input("Observações")
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    submitted = st.form_submit_button("Salvar", use_container_width=True)
                with col_b2:
                    cancel = st.form_submit_button("Cancelar", use_container_width=True)
                
                if cancel:
                    st.session_state.show_new_appointment = False
                    st.rerun()
                
                if submitted and patient_options:
                    data = {
                        "patient_id": patient_options[selected_patient],
                        "professional_id": professional_id,
                        "appointment_date": appt_date.isoformat(),
                        "start_time": start_time.strftime("%H:%M"),
                        "appointment_type": appt_type,
                        "value": value,
                        "notes": notes,
                        "status": "agendado"
                    }
                    db.create_appointment(data)
                    st.success("Agendamento criado!")
                    st.session_state.show_new_appointment = False
                    st.rerun()
    
    # ====================== LISTA RÁPIDA DE AGENDAMENTOS ======================
    st.markdown("---")
    st.markdown("### Lista de Agendamentos da Semana")
    
    if appointments:
        df = pd.DataFrame(appointments)
        df_display = df[["appointment_date", "start_time", "patient_name", "appointment_type", "status", "value"]].copy()
        df_display.columns = ["Data", "Horário", "Paciente", "Tipo", "Status", "Valor"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Atualizar status
        st.markdown("#### Atualizar Status de um Agendamento")
        selected_id = st.selectbox(
            "Selecione o agendamento",
            options=[a["id"] for a in appointments],
            format_func=lambda x: next(
                f"{a['appointment_date']} {a['start_time']} - {a['patient_name']}" 
                for a in appointments if a["id"] == x
            )
        )
        new_status = st.selectbox("Novo Status", ["agendado", "confirmado", "realizado", "faltou", "cancelado"])
        if st.button("Atualizar Status"):
            db.update_appointment_status(selected_id, new_status)
            st.success("Status atualizado!")
            st.rerun()
    else:
        st.info("Nenhum agendamento encontrado nesta semana para este profissional.")

def page_financial():
    user = st.session_state.user
    is_admin = user["role"] == "admin"
    
    st.title("💰 Controle Financeiro")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("De", value=date.today().replace(day=1), key="fin_from")
    with col2:
        date_to = st.date_input("Até", value=date.today(), key="fin_to")
    
    summary = db.get_financial_summary(
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat()
    )
    
    st.markdown("### 📈 Resumo do Período")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Recebido", format_currency(summary["geral"]["total_pago"]))
    with c2:
        st.metric("Total Pendente", format_currency(summary["geral"]["total_pendente"]))
    with c3:
        st.metric("Lançamentos", summary["geral"]["total_lancamentos"])
    
    if is_admin:
        st.markdown("### 👨‍⚕️ Receita por Profissional")
        if summary["por_profissional"]:
            df_prof = pd.DataFrame(summary["por_profissional"])
            df_prof = df_prof[["name", "total_pago", "total_pendente", "qtd_lancamentos"]]
            df_prof.columns = ["Profissional", "Recebido", "Pendente", "Qtd Lançamentos"]
            df_prof["Recebido"] = df_prof["Recebido"].apply(format_currency)
            df_prof["Pendente"] = df_prof["Pendente"].apply(format_currency)
            st.dataframe(df_prof, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum dado por profissional ainda.")
    
    st.markdown("---")
    
    st.markdown("### ➕ Novo Lançamento Financeiro")
    with st.form("new_payment"):
        patients = db.get_patients()
        patient_opts = {f"{p['full_name']}": p['id'] for p in patients}
        patient_opts["(Sem paciente específico)"] = None
        
        professionals = db.get_all_professionals()
        if is_admin:
            prof_opts = {p["name"]: p["id"] for p in professionals}
            prof_opts["(Não vinculado)"] = None
        else:
            prof_opts = {user["name"]: user["id"]}
        
        c1, c2 = st.columns(2)
        with c1:
            selected_patient = st.selectbox("Paciente", list(patient_opts.keys()))
            amount = st.number_input("Valor (R$) *", min_value=0.0, step=10.0)
            payment_date = st.date_input("Data do Pagamento", value=date.today())
        with c2:
            selected_prof = st.selectbox("Profissional", list(prof_opts.keys()))
            payment_method = st.selectbox("Forma de Pagamento", ["PIX", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Convênio", "Transferência"])
            status = st.selectbox("Status", ["pago", "pendente"])
            description = st.text_input("Descrição")
        
        if st.form_submit_button("Registrar Pagamento"):
            if amount <= 0:
                st.error("Informe um valor válido")
            else:
                data = {
                    "patient_id": patient_opts[selected_patient],
                    "professional_id": prof_opts[selected_prof],
                    "amount": amount,
                    "payment_date": payment_date.isoformat(),
                    "payment_method": payment_method,
                    "status": status,
                    "description": description,
                    "created_by": user["id"]
                }
                db.create_payment(data)
                st.success("Lançamento registrado!")
                st.rerun()
    
    st.markdown("### 📋 Lançamentos")
    payments = db.get_payments(
        professional_id=None if is_admin else user["id"],
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat()
    )
    
    if payments:
        df = pd.DataFrame(payments)
        cols = ["payment_date", "patient_name", "professional_name", "amount", "payment_method", "status", "description"]
        df_display = df[cols].copy()
        df_display.columns = ["Data", "Paciente", "Profissional", "Valor", "Forma", "Status", "Descrição"]
        df_display["Valor"] = df_display["Valor"].apply(format_currency)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento no período.")


def page_professionals():
    st.title("👨‍⚕️ Profissionais")
    st.markdown("---")
    
    if st.session_state.user["role"] != "admin":
        st.error("Acesso restrito ao administrador")
        return
    
    professionals = db.get_all_professionals()
    
    st.markdown("### Profissionais Cadastrados")
    if professionals:
        for p in professionals:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{p['name']}** (@{p['username']})")
            with col2:
                st.write(p['phone'] or "-")
            with col3:
                st.write("✅ Ativo" if p['active'] else "❌ Inativo")
    else:
        st.info("Nenhum profissional cadastrado ainda.")
    
    st.markdown("---")
    st.markdown("### ➕ Cadastrar Novo Profissional")
    
    with st.form("new_professional"):
        name = st.text_input("Nome Completo *")
        username = st.text_input("Nome de Usuário (login) *")
        password = st.text_input("Senha *", type="password")
        phone = st.text_input("Telefone")
        
        if st.form_submit_button("Cadastrar Profissional"):
            if not name or not username or not password:
                st.error("Preencha os campos obrigatórios")
            else:
                success, msg = db.create_user(name, username, password, role="professional", phone=phone)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# ====================== MAIN ======================

def main():
    if not check_login():
        login_page()
        return
    
    if st.session_state.get("page_mode") == "patient_detail":
        page_patient_detail()
        return
    
    choice = sidebar()
    
    if choice == "🏠 Início":
        page_home()
    elif choice in ["👥 Pacientes Ativos", "👥 Meus Pacientes Ativos"]:
        page_patients(status="ativo")
    elif choice in ["📂 Pacientes Inativos (Histórico)", "📂 Meus Pacientes Inativos"]:
        page_patients(status="inativo")
    elif choice in ["📅 Agenda Geral", "📅 Minha Agenda"]:
        page_agenda()
    elif choice in ["💰 Controle Financeiro", "💰 Meus Atendimentos / Financeiro"]:
        page_financial()
    elif choice == "👨‍⚕️ Profissionais":
        page_professionals()
    elif choice == "📝 Evoluções":
        st.title("📝 Evoluções")
        st.info("Acesse o paciente desejado em 'Meus Pacientes' e registre a evolução lá.")
    elif choice == "📊 Relatórios":
        st.title("📊 Relatórios")
        st.info("Em desenvolvimento — em breve relatórios mais detalhados.")

if __name__ == "__main__":
    main()
