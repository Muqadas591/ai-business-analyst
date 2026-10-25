"""Streamlit UI for local username/password authentication."""

from __future__ import annotations

import logging

import streamlit as st
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from business_analyst.auth_models import AppUser
from business_analyst.auth_service import (
    AuthenticationError,
    authenticate_user,
    register_user,
)
from business_analyst.database import SessionLocal
from business_analyst.security.identity import AuthenticatedPrincipal
from business_analyst.workspaces.access import WorkspaceAccessService
from business_analyst.workspaces.models import (
    Workspace,
    WorkspaceMembership,
)

logger = logging.getLogger(__name__)

_AUTH_USER_KEY = "_local_authenticated_user_id"


def _render_login() -> None:
    """Display login and registration forms."""
    st.title("AI Business Analyst")
    st.subheader("Sign in to your account")
    st.caption("Sign in or create an account to access your workspaces.")

    login_tab, register_tab = st.tabs(["Sign in", "Create account"])

    with login_tab:
        with st.form("local_login_form"):
            username = st.text_input(
                "Username",
                key="login_username",
            )
            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )

            submitted = st.form_submit_button(
                "Sign in",
                use_container_width=True,
            )

        if submitted:
            try:
                with SessionLocal() as session:
                    user = authenticate_user(
                        session,
                        username=username,
                        password=password,
                    )
                    user_id = user.id

                # Set identity only after the database verified the password.
                st.session_state[_AUTH_USER_KEY] = user_id
                st.rerun()

            except AuthenticationError as exc:
                st.error(str(exc))

            except Exception:
                logger.exception("Login operation failed.")
                st.error("Unable to sign in right now. Please try again.")

    with register_tab:
        st.write("Create an account to get your own workspace.")

        with st.form("local_register_form"):
            new_username = st.text_input(
                "Choose a username",
                key="register_username",
            )
            new_password = st.text_input(
                "Create a password",
                type="password",
                key="register_password",
            )
            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="register_password_confirm",
            )

            submitted = st.form_submit_button(
                "Create account",
                use_container_width=True,
            )

        if submitted:
            if new_password != confirm_password:
                st.error("The passwords do not match.")
            else:
                try:
                    with SessionLocal() as session:
                        user = register_user(
                            session,
                            username=new_username,
                            password=new_password,
                        )
                        user_id = user.id

                    st.session_state[_AUTH_USER_KEY] = user_id
                    st.success("Account created successfully.")
                    st.rerun()

                except (ValueError, AuthenticationError) as exc:
                    st.error(str(exc))

                except IntegrityError:
                    st.error(
                        "Unable to register with that username. Please choose another."
                    )

                except Exception:
                    logger.exception("Registration operation failed.")
                    st.error(
                        "Unable to create your account right now. Please try again."
                    )


def render_authentication_and_workspace_selector() -> dict:
    """Authenticate a user and return a verified workspace context."""
    user_id = st.session_state.get(_AUTH_USER_KEY)

    if not isinstance(user_id, str) or not user_id:
        _render_login()
        st.stop()

    session = SessionLocal()

    try:
        user = session.scalar(
            select(AppUser).where(
                AppUser.id == user_id,
                AppUser.is_active.is_(True),
            )
        )

        if user is None:
            session.close()
            st.session_state.pop(_AUTH_USER_KEY, None)
            st.warning("Your session is no longer valid. Please sign in again.")
            st.rerun()

        principal = AuthenticatedPrincipal(user_id=user.id)
        access = WorkspaceAccessService(session)

        statement = (
            select(Workspace)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == Workspace.id,
            )
            .where(
                WorkspaceMembership.user_id == user.id,
                Workspace.is_active.is_(True),
            )
            .order_by(Workspace.name)
        )

        workspaces = list(session.scalars(statement).all())

        st.sidebar.caption(f"Signed in as **{user.username}**")

        if st.sidebar.button("Log out", use_container_width=True):
            session.close()
            st.session_state.pop(_AUTH_USER_KEY, None)
            st.session_state.pop("_active_workspace_namespace", None)
            st.rerun()

        st.sidebar.divider()
        st.sidebar.subheader("Workspace")

        if not workspaces:
            st.info("You do not have a workspace yet.")

            with st.form("create_first_workspace_form"):
                workspace_name = st.text_input(
                    "Workspace name",
                    max_chars=120,
                )
                submitted = st.form_submit_button("Create workspace")

            if submitted:
                try:
                    access.create_workspace(
                        authenticated_user_id=user.id,
                        name=workspace_name,
                    )
                    session.commit()
                    st.rerun()

                except Exception:
                    session.rollback()

                    # Avoid displaying database details to the user.
                    logger.exception("Workspace creation failed.")
                    st.error(
                        "Unable to create the workspace. "
                        "Check the workspace name and try again."
                    )

            session.close()
            st.stop()

        selected_workspace = st.sidebar.selectbox(
            "Select workspace",
            options=workspaces,
            format_func=lambda workspace: workspace.name,
            key="_selected_workspace_object",
        )

        # Verify membership again before returning the selected context.
        verified_workspace = access.get_accessible_workspace(
            authenticated_user_id=user.id,
            workspace_id=selected_workspace.id,
        )

        return {
            "verified_user": principal,
            "db_session": session,
            "selected_workspace_id": verified_workspace.id,
        }

    except Exception:
        session.close()
        raise
