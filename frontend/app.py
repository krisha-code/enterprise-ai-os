import os
import requests
import secrets
import streamlit as st


def get_api_url():
    """Use the deployed API URL when configured, otherwise use local Docker."""
    api_url = os.getenv("API_URL")
    if not api_url:
        try:
            api_url = st.secrets["API_URL"]
        except (FileNotFoundError, KeyError):
            api_url = "http://127.0.0.1:8000"
    return api_url.rstrip("/")


API_URL = get_api_url()


def ensure_conversation(auth_headers):
    if "conversation_id" not in st.session_state:
        response = requests.post(
            f"{API_URL}/conversations",
            headers=auth_headers,
            json={"title": "Document Q&A"},
            timeout=15,
        )
        response.raise_for_status()
        st.session_state["conversation_id"] = response.json()["id"]
    return st.session_state["conversation_id"]


def send_chat(auth_headers, question, mode, document_id):
    conversation_id = ensure_conversation(auth_headers)
    payload = {"question": question, "mode": mode}
    if document_id is not None:
        payload["document_id"] = document_id

    response = requests.post(
        f"{API_URL}/conversations/{conversation_id}/chat",
        headers=auth_headers,
        json=payload,
        timeout=(10, 600 if mode == "document_summary" else 180),
    )
    response.raise_for_status()
    result = response.json()
    st.session_state["chat_history"].append(
        {
            "question": question,
            "answer": result["answer"],
            "citations": result.get("citations", []),
            "mode": mode,
        }
    )
    st.session_state["opened_history"] = []
    return result


def show_result(title, question, result):
    st.markdown(f"#### {title}")
    st.info(f"**You asked:** {question}")
    with st.container(border=True):
        st.markdown("**AI response**")
        st.markdown(result["answer"])
        citations = result.get("citations", [])
        if citations:
            with st.expander("Sources"):
                for citation in citations:
                    source = f"**{citation['filename']}**"
                    if citation.get("section_title"):
                        source += f" — {citation['section_title']}"
                    if citation.get("page_number") is not None:
                        source += f" (page {citation['page_number']})"
                    st.markdown(f"- {source}")

st.set_page_config(page_title="Enterprise AI OS", page_icon="📚")
st.title("Enterprise AI OS")
st.caption("Secure, organization-aware document question answering")

if not st.session_state.get("access_token"):
    st.subheader("Sign in")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        try:
            response = requests.post(
                f"{API_URL}/auth/login",
                data={"username": email, "password": password},
                timeout=10,
            )
            if response.ok:
                tokens = response.json()
                st.session_state["access_token"] = tokens["access_token"]
                st.session_state["refresh_token"] = tokens["refresh_token"]
                st.session_state["user_email"] = email
                identity_response = requests.get(
                    f"{API_URL}/auth/me",
                    headers={"Authorization": f"Bearer {tokens['access_token']}"},
                    timeout=10,
                )
                identity_response.raise_for_status()
                st.session_state["account"] = identity_response.json()
                st.rerun()
            else:
                try:
                    message = response.json().get(
                        "detail", "Please check your email and password."
                    )
                except ValueError:
                    message = "Please check your email and password."
                st.error(f"Sign-in failed: {message}")
        except requests.RequestException as error:
            st.error(f"Could not reach the backend: {error}")

if st.session_state.get("access_token"):
    auth_headers = {
        "Authorization": f"Bearer {st.session_state['access_token']}"
    }
    account = st.session_state.get("account")
    if account is None:
        try:
            identity_response = requests.get(
                f"{API_URL}/auth/me",
                headers=auth_headers,
                timeout=10,
            )
            identity_response.raise_for_status()
            account = identity_response.json()
            st.session_state["account"] = account
        except requests.HTTPError as error:
            st.error("Your sign-in session is no longer valid. Please sign in again.")
            st.session_state.pop("access_token", None)
            st.session_state.pop("refresh_token", None)
            st.session_state.pop("account", None)
            st.stop()
        except requests.RequestException as error:
            st.error(f"Could not verify your account: {error}")
            st.stop()

    role_label = "Organization Admin" if account["role"] == "admin" else "Regular User"
    account_col, logout_col = st.columns([5, 1])
    with account_col:
        st.success(
            f"Signed in as {account['email']} · **{role_label}** · "
            f"Organization #{account['organization_id']}"
        )
    with logout_col:
        if st.button("Sign out", key="sign_out"):
            try:
                requests.post(
                    f"{API_URL}/auth/logout",
                    json={"refresh_token": st.session_state.get("refresh_token", "")},
                    timeout=10,
                )
            except requests.RequestException:
                pass
            for key in (
                "access_token", "refresh_token", "user_email", "account",
                "conversation_id", "chat_history", "mode_results",
                "combined_results", "opened_history", "admin_created_account",
            ):
                st.session_state.pop(key, None)
            st.rerun()

    if account["must_change_password"]:
        st.warning(
            "Your account was created with a temporary password. Change it before using the workspace."
        )
        with st.form("required_password_change"):
            temporary_password = st.text_input("Temporary password", type="password")
            new_password = st.text_input(
                "New password (at least 12 characters)", type="password"
            )
            confirm_password = st.text_input("Confirm new password", type="password")
            change_submitted = st.form_submit_button("Change password")
        if change_submitted:
            if new_password != confirm_password:
                st.error("The new passwords do not match.")
            else:
                try:
                    change_response = requests.post(
                        f"{API_URL}/auth/change-password",
                        headers=auth_headers,
                        json={
                            "current_password": temporary_password,
                            "new_password": new_password,
                        },
                        timeout=15,
                    )
                    change_response.raise_for_status()
                    st.success("Password changed. Sign in again with your new password.")
                    for key in ("access_token", "refresh_token", "user_email", "account"):
                        st.session_state.pop(key, None)
                    st.rerun()
                except requests.HTTPError as error:
                    st.error(f"Password change failed: {error.response.text}")
                except requests.RequestException as error:
                    st.error(f"Could not reach the backend: {error}")
        st.stop()

    if account["role"] == "admin":
        with st.expander("Organization admin · Manage users"):
            st.caption(
                "You can create regular users and enable or disable accounts in your organization. "
                "Users cannot grant themselves admin access."
            )
            with st.form("create_organization_user"):
                new_user_name = st.text_input("Employee name")
                new_user_email = st.text_input("Employee email")
                create_user_submitted = st.form_submit_button("Create regular-user account")
            if create_user_submitted:
                if not new_user_name.strip() or not new_user_email.strip():
                    st.warning("Enter the employee's name and email.")
                else:
                    temporary_password = secrets.token_urlsafe(18)
                    try:
                        create_response = requests.post(
                            f"{API_URL}/users/",
                            headers=auth_headers,
                            json={
                                "name": new_user_name.strip(),
                                "email": new_user_email.strip(),
                                "password": temporary_password,
                            },
                            timeout=15,
                        )
                        create_response.raise_for_status()
                        st.session_state["admin_created_account"] = {
                            "email": new_user_email.strip(),
                            "temporary_password": temporary_password,
                        }
                        st.success("Regular-user account created.")
                    except requests.HTTPError as error:
                        st.error(f"Could not create account: {error.response.text}")
                    except requests.RequestException as error:
                        st.error(f"Could not reach the backend: {error}")

            created_account = st.session_state.get("admin_created_account")
            if created_account:
                st.warning(
                    f"Give this temporary password to {created_account['email']} through a private channel. "
                    "It is shown here only so you can pass it to them; they must change it at first sign-in."
                )
                st.code(created_account["temporary_password"])
                if st.button("Hide temporary password", key="hide_created_password"):
                    st.session_state.pop("admin_created_account", None)
                    st.rerun()

            try:
                users_response = requests.get(
                    f"{API_URL}/users/admin/all",
                    headers=auth_headers,
                    timeout=15,
                )
                users_response.raise_for_status()
                organization_users = users_response.json()
                st.markdown("**Accounts in your organization**")
                for managed_user in organization_users:
                    user_col, action_col = st.columns([4, 1])
                    with user_col:
                        account_state = "Active" if managed_user["is_active"] else "Disabled"
                        st.write(
                            f"**{managed_user['name']}** · {managed_user['email']} · "
                            f"{account_state} · "
                            f"{managed_user['role_name'].replace('_', ' ').title()}"
                        )
                    with action_col:
                        is_self = account.get("id") == managed_user["id"]
                        action = "Deactivate" if managed_user["is_active"] else "Activate"
                        if st.button(
                            action,
                            key=f"manage_user_{managed_user['id']}",
                            disabled=is_self,
                        ):
                            try:
                                action_response = requests.patch(
                                    f"{API_URL}/users/{managed_user['id']}/"
                                    f"{'deactivate' if managed_user['is_active'] else 'activate'}",
                                    headers=auth_headers,
                                    timeout=15,
                                )
                                action_response.raise_for_status()
                                st.rerun()
                            except requests.HTTPError as error:
                                st.error(f"Account update failed: {error.response.text}")
                            except requests.RequestException as error:
                                st.error(f"Could not reach the backend: {error}")
            except requests.HTTPError as error:
                st.error(f"Could not load organization accounts: {error.response.text}")
            except requests.RequestException as error:
                st.error(f"Could not reach the backend: {error}")

    st.subheader("Upload a document")
    uploaded_file = st.file_uploader(
        "Choose a PDF, DOCX, or TXT file (maximum 10 MB)",
        type=["pdf", "docx", "txt"],
    )

    if st.button("Upload document", disabled=uploaded_file is None):
        try:
            with st.spinner("Uploading and processing document..."):
                upload_response = requests.post(
                    f"{API_URL}/documents/upload",
                    headers=auth_headers,
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream",
                        )
                    },
                    timeout=(10, 300),
                )
            upload_response.raise_for_status()
            uploaded_document = upload_response.json()
            st.success(
                f"Uploaded {uploaded_document['filename']} "
                f"(status: {uploaded_document['status']})."
            )
            st.rerun()
        except requests.HTTPError as error:
            st.error(f"Upload failed: {error.response.text}")
        except requests.RequestException as error:
            st.error(f"Could not reach the backend: {error}")

    st.subheader("Organization documents")
    documents = []
    try:
        document_response = requests.get(
            f"{API_URL}/documents/",
            headers=auth_headers,
            timeout=15,
        )
        document_response.raise_for_status()
        documents = document_response.json()

        if documents:
            st.dataframe(
                [
                    {
                        "ID": document["id"],
                        "Filename": document["filename"],
                        "Status": document["processing_status"],
                    }
                    for document in documents
                ],
                hide_index=True,
            )
        else:
            st.info("No documents are available to this organization yet.")
    except requests.RequestException as error:
        st.error(f"Could not load documents: {error}")

    available_documents = [
        document
        for document in documents
        if document["processing_status"] == "completed"
    ]
    document_scope_options = ["All organization documents"] + [
        f"{document['filename']} (#{document['id']})"
        for document in available_documents
    ]
    document_ids_by_scope = {
        f"{document['filename']} (#{document['id']})": document["id"]
        for document in available_documents
    }

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "mode_results" not in st.session_state:
        st.session_state["mode_results"] = {}
    if "combined_results" not in st.session_state:
        st.session_state["combined_results"] = []
    if "opened_history" not in st.session_state:
        st.session_state["opened_history"] = []

    st.subheader("Document workspace")
    selected_scope = st.selectbox(
        "Use documents from",
        document_scope_options,
        key="chat_document_scope",
    )
    selected_document_id = document_ids_by_scope.get(selected_scope)
    if selected_document_id is None:
        st.caption("The AI can search across completed documents in your organization.")
    else:
        st.caption(f"The AI will use only {selected_scope}.")

    workspace_section = st.radio(
        "Choose what you want to do",
        [
            "Ask",
            "Summarize passages",
            "Whole-document summary",
            "Run all three",
            "Search",
            "History",
        ],
        horizontal=True,
        key="workspace_section",
    )

    if workspace_section == "Ask":
        st.markdown("### Ask a question")
        with st.form("ask_form"):
            ask_question = st.text_area(
                "Question",
                placeholder="For example: How does the report describe login security?",
                height=100,
            )
            ask_submitted = st.form_submit_button("Get answer")
        if ask_submitted:
            if not ask_question.strip():
                st.warning("Enter a question first.")
            else:
                try:
                    with st.spinner("Finding evidence and preparing an answer..."):
                        result = send_chat(
                            auth_headers,
                            ask_question.strip(),
                            "answer",
                            selected_document_id,
                        )
                    st.session_state["mode_results"]["answer"] = {
                        "question": ask_question.strip(),
                        "result": result,
                    }
                except requests.HTTPError as error:
                    st.error(f"Question failed: {error.response.text}")
                except requests.RequestException as error:
                    st.error(f"Could not reach the backend: {error}")
        saved = st.session_state["mode_results"].get("answer")
        if saved:
            show_result("Answer", saved["question"], saved["result"])

    elif workspace_section == "Summarize passages":
        st.markdown("### Summarize matching passages")
        st.caption("Enter a topic or question. The system finds relevant passages and summarizes them together.")
        with st.form("passage_summary_form"):
            passage_focus = st.text_area(
                "Topic to summarize",
                placeholder="For example: face model architecture and training",
                height=100,
            )
            passage_submitted = st.form_submit_button("Summarize passages")
        if passage_submitted:
            if not passage_focus.strip():
                st.warning("Enter a topic so the system knows which passages to find.")
            else:
                try:
                    with st.spinner("Finding and synthesizing relevant passages..."):
                        result = send_chat(
                            auth_headers,
                            passage_focus.strip(),
                            "passage_summary",
                            selected_document_id,
                        )
                    st.session_state["mode_results"]["passages"] = {
                        "question": passage_focus.strip(),
                        "result": result,
                    }
                except requests.HTTPError as error:
                    st.error(f"Passage summary failed: {error.response.text}")
                except requests.RequestException as error:
                    st.error(f"Could not reach the backend: {error}")
        saved = st.session_state["mode_results"].get("passages")
        if saved:
            show_result("Matching-passage summary", saved["question"], saved["result"])

    elif workspace_section == "Whole-document summary":
        st.markdown("### Summarize one complete document")
        if selected_document_id is None:
            st.info("Choose one document in the selector above to create a whole-document summary.")
        elif st.button("Create whole-document summary", key="whole_document_summary"):
            summary_question = (
                "Give a concise, well-organized summary of this document's "
                "main topic, key points, and conclusions."
            )
            try:
                with st.spinner("Reading the full document and preparing one coherent overview..."):
                    result = send_chat(
                        auth_headers,
                        summary_question,
                        "document_summary",
                        selected_document_id,
                    )
                st.session_state["mode_results"]["document"] = {
                    "question": selected_scope,
                    "result": result,
                }
            except requests.HTTPError as error:
                st.error(f"Document summary failed: {error.response.text}")
            except requests.RequestException as error:
                st.error(f"Could not reach the backend: {error}")
        saved = st.session_state["mode_results"].get("document")
        if saved:
            show_result("Whole-document overview", saved["question"], saved["result"])

    elif workspace_section == "Run all three":
        st.markdown("### Run all three modes")
        st.caption("This returns a direct answer, a summary of matching passages, and a whole-document overview in separate result cards.")
        with st.form("combined_form"):
            combined_question = st.text_area(
                "Question or topic",
                placeholder="For example: How does MindSense combine the three modalities?",
                height=100,
            )
            combined_submitted = st.form_submit_button(
                "Run all three",
                disabled=selected_document_id is None,
            )
        if selected_document_id is None:
            st.info("Select one document above before running all three modes.")
        if combined_submitted:
            if not combined_question.strip():
                st.warning("Enter a question or topic first.")
            else:
                focus = combined_question.strip()
                modes = [
                    ("Direct answer", "answer", focus),
                    ("Matching-passage summary", "passage_summary", focus),
                    (
                        "Whole-document overview",
                        "document_summary",
                        "Give a concise, well-organized summary of this "
                        "document's main topic, key points, and conclusions.",
                    ),
                ]
                combined_results = []
                try:
                    for title, mode, prompt in modes:
                        with st.spinner(f"Preparing {title.lower()}..."):
                            result = send_chat(
                                auth_headers,
                                prompt,
                                mode,
                                selected_document_id,
                            )
                        combined_results.append(
                            {"title": title, "question": focus, "result": result}
                        )
                    st.session_state["combined_results"] = combined_results
                except requests.HTTPError as error:
                    st.error(f"Combined run failed: {error.response.text}")
                except requests.RequestException as error:
                    st.error(f"Could not reach the backend: {error}")
        for item in st.session_state["combined_results"]:
            show_result(item["title"], item["question"], item["result"])

    elif workspace_section == "Search":
        st.markdown("### Find matching text without generating an answer")
        st.caption("Search shows the stored passages that match your terms. Use Ask or a summary mode when you want an AI response.")
        with st.form("document_search_form"):
            search_scope = st.selectbox(
                "Search within",
                document_scope_options,
                key="search_document_scope",
            )
            search_query = st.text_input("Search terms")
            search_limit = st.slider(
                "Maximum results",
                min_value=1,
                max_value=10,
                value=5,
            )
            search_submitted = st.form_submit_button("Search")
        if search_submitted:
            if not search_query.strip():
                st.warning("Enter search terms first.")
            else:
                try:
                    search_params = {
                        "query": search_query.strip(),
                        "limit": search_limit,
                    }
                    search_document_id = document_ids_by_scope.get(search_scope)
                    if search_document_id is not None:
                        search_params["document_id"] = search_document_id
                    search_response = requests.get(
                        f"{API_URL}/documents/search",
                        headers=auth_headers,
                        params=search_params,
                        timeout=30,
                    )
                    search_response.raise_for_status()
                    search_results = search_response.json()
                    if search_results:
                        st.caption(f"Found {len(search_results)} matching passages.")
                        filenames_by_id = {
                            document["id"]: document["filename"]
                            for document in documents
                        }
                        for match in search_results:
                            filename = filenames_by_id.get(
                                match["document_id"],
                                f"Document {match['document_id']}",
                            )
                            with st.expander(
                                f"{filename} · passage {match['chunk_index'] + 1}"
                            ):
                                st.write(match["content"])
                    else:
                        st.info("No matching text found in this organization's documents.")
                except requests.HTTPError as error:
                    st.error(f"Search failed: {error.response.text}")
                except requests.RequestException as error:
                    st.error(f"Could not reach the backend: {error}")

    else:
        st.markdown("### Conversation history")
        st.caption("Choose a saved conversation and open it to view its previous questions and answers.")
        try:
            conversations_response = requests.get(
                f"{API_URL}/conversations",
                headers=auth_headers,
                timeout=15,
            )
            conversations_response.raise_for_status()
            conversations = conversations_response.json()
            if conversations:
                conversation_labels = {
                    f"{item['title']} (#{item['id']})": item["id"]
                    for item in conversations
                }
                history_choice = st.selectbox(
                    "Saved conversations",
                    list(conversation_labels),
                    key="saved_conversation_choice",
                )
                if st.button("Open conversation history"):
                    history_id = conversation_labels[history_choice]
                    messages_response = requests.get(
                        f"{API_URL}/conversations/{history_id}/messages",
                        headers=auth_headers,
                        timeout=15,
                    )
                    messages_response.raise_for_status()
                    loaded_history = []
                    pending_question = ""
                    for message in messages_response.json():
                        if message["role"] == "user":
                            pending_question = message["content"]
                        elif message["role"] == "assistant":
                            loaded_history.append(
                                {
                                    "question": pending_question,
                                    "answer": message["content"],
                                    "citations": [],
                                    "mode": "history",
                                }
                            )
                            pending_question = ""
                    st.session_state["conversation_id"] = history_id
                    st.session_state["chat_history"] = loaded_history
                    st.session_state["opened_history"] = loaded_history
                    st.rerun()
            else:
                st.info("No saved conversations yet.")
        except requests.RequestException as error:
            st.error(f"Could not load saved conversations: {error}")

        if st.button("Start a new conversation"):
            st.session_state.pop("conversation_id", None)
            st.session_state["chat_history"] = []
            st.session_state["opened_history"] = []
            st.session_state["mode_results"] = {}
            st.session_state["combined_results"] = []
            st.rerun()

        history_to_show = (
            st.session_state["opened_history"]
            if st.session_state["opened_history"]
            else st.session_state["chat_history"]
        )
        if history_to_show:
            st.markdown("#### Messages")
            for exchange in history_to_show:
                st.info(f"**You asked:** {exchange['question']}")
                with st.container(border=True):
                    st.markdown("**AI response**")
                    st.markdown(exchange["answer"])
        else:
            st.info("Open a saved conversation to see its messages here.")

st.divider()
st.subheader("Backend status")

try:
    health_response = requests.get(f"{API_URL}/health", timeout=5)
    health_response.raise_for_status()
    st.success("Backend is connected")
    st.json(health_response.json())
except requests.RequestException as error:
    st.error(f"Could not connect to the backend: {error}")
