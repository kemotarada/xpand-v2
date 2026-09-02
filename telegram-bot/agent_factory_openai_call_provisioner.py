# =========================================================
# XPAND AGENT FACTORY
# OPENAI LIVE CALL PROVISIONER V2.2
#
# XPAND LIVE CALL
#
# Telegram WebApp
#      ↓
# WebRTC
#      ↓
# OpenAI Realtime
#
# V2.2 FIX:
# - Railway GraphQL now uses requests, not urllib
# - Railway official token headers supported
# - Account / Workspace token -> Authorization: Bearer
# - Project token -> Project-Access-Token
# - NO automatic retry for Railway mutations
# - Cloudflare 403 / 1010 is surfaced clearly
#
# This wrapper preserves:
# - Kemo -> Gemini
# - XPAND text -> OpenAI
# - XPAND Telegram voice -> OpenAI
# - XPAND AI policy
# - Existing Agent Factory
# - Existing natural command router
#
# No fake verification.
# =========================================================


import os
import json
import time
import secrets

from datetime import datetime, timezone


# =========================================================
# REQUESTS
#
# Do not crash Kemo startup if requests is missing.
# Provisioning will be blocked with a clear message.
# =========================================================

try:
    import requests

except ImportError:
    requests = None


# =========================================================
# EXISTING VERIFIED STACK
# =========================================================

import agent_factory_ai_policy as ai_policy


providers = ai_policy.providers

call_stack = providers.call_stack

factory = call_stack.factory

profiles = call_stack.profiles

capabilities = call_stack.capabilities

kemo = call_stack.kemo


# =========================================================
# VERSION
# =========================================================

VERSION = "2.2"


# =========================================================
# RAILWAY CONFIG
# =========================================================

RAILWAY_GRAPHQL_URL = (
    "https://backboard.railway.com/graphql/v2"
)


GITHUB_REPO = str(
    os.getenv(
        "AGENT_FACTORY_GITHUB_REPO",
        "kemotarada/kemo-telegram-bot"
    )
).strip()


CALL_ROOT_DIRECTORY = (
    "/agent_templates/live_call"
)


CALL_START_COMMAND = (
    "npm start"
)


CALL_HEALTH_PATH = (
    "/api/health"
)


# =========================================================
# OPENAI REALTIME CONFIG
# =========================================================

REALTIME_MODEL = str(
    os.getenv(
        "XPAND_REALTIME_MODEL",
        "gpt-realtime-2.1"
    )
).strip()


TRANSCRIBE_MODEL = str(
    os.getenv(
        "XPAND_TRANSCRIBE_MODEL",
        "gpt-realtime-whisper"
    )
).strip()


REALTIME_VOICE = str(
    os.getenv(
        "XPAND_REALTIME_VOICE",
        "marin"
    )
).strip()


TIMEZONE = str(
    os.getenv(
        "XPAND_TIMEZONE",
        "Asia/Hebron"
    )
).strip()


DEPLOY_TIMEOUT_SECONDS = max(
    180,
    int(
        os.getenv(
            "XPAND_CALL_DEPLOY_TIMEOUT_SECONDS",
            "720"
        )
        or
        "720"
    )
)


HEALTH_TIMEOUT_SECONDS = max(
    60,
    int(
        os.getenv(
            "XPAND_CALL_HEALTH_TIMEOUT_SECONDS",
            "240"
        )
        or
        "240"
    )
)


POLL_SECONDS = 5


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value,
    max_length=5000
):
    return (
        str(
            value
            if value is not None
            else
            ""
        )
        .replace(
            "\x00",
            ""
        )
        .strip()[:max_length]
    )


def now_utc():

    return datetime.now(
        timezone.utc
    )


def parse_json_value(
    value,
    default
):

    if isinstance(
        value,
        type(
            default
        )
    ):

        return value

    if isinstance(
        value,
        str
    ):

        try:

            parsed = json.loads(
                value
            )

            if isinstance(
                parsed,
                type(
                    default
                )
            ):

                return parsed

        except Exception:
            pass

    return default


# =========================================================
# XPAND SECRETS
# =========================================================

def xpand_openai_key():

    return clean_text(
        os.getenv(
            "XPAND_OPENAI_API_KEY"
        ),
        100000
    )


def xpand_database_url():

    return clean_text(
        os.getenv(
            "XPAND_DATABASE_URL"
        ),
        100000
    )


# =========================================================
# RAILWAY AUTH
#
# Railway official authentication:
#
# Account / Workspace:
# Authorization: Bearer TOKEN
#
# Project:
# Project-Access-Token: TOKEN
#
# Explicit RAILWAY_PROJECT_TOKEN always wins.
# =========================================================

def railway_auth_config():

    project_token = clean_text(
        os.getenv(
            "RAILWAY_PROJECT_TOKEN"
        ),
        10000
    )

    if project_token:

        return {
            "mode":
                "project",

            "token":
                project_token
        }

    bearer_token = clean_text(
        os.getenv(
            "RAILWAY_API_TOKEN"
        )
        or
        os.getenv(
            "RAILWAY_TOKEN"
        ),
        10000
    )

    if bearer_token:

        return {
            "mode":
                "bearer",

            "token":
                bearer_token
        }

    return {
        "mode":
            "",

        "token":
            ""
    }


def railway_token_compat():

    return railway_auth_config().get(
        "token"
    ) or ""


def railway_token_ready():

    auth = railway_auth_config()

    return bool(
        auth.get(
            "token"
        )
    )


# =========================================================
# RAILWAY RESPONSE HELPERS
# =========================================================

def railway_response_excerpt(
    response,
    limit=2500
):

    try:

        data = response.json()

        return clean_text(
            json.dumps(
                data,
                ensure_ascii=False
            ),
            limit
        )

    except Exception:

        return clean_text(
            getattr(
                response,
                "text",
                ""
            ),
            limit
        )


def railway_graphql_error_messages(
    errors
):

    messages = []

    if not isinstance(
        errors,
        list
    ):

        return messages

    for item in errors:

        if not isinstance(
            item,
            dict
        ):

            continue

        message = clean_text(
            item.get(
                "message"
            ),
            1200
        )

        if message:

            messages.append(
                message
            )

        extensions = item.get(
            "extensions"
        )

        if isinstance(
            extensions,
            dict
        ):

            code = clean_text(
                extensions.get(
                    "code"
                ),
                200
            )

            if (
                code
                and
                code
                not in messages
            ):

                messages.append(
                    "code="
                    +
                    code
                )

    return messages


# =========================================================
# RAILWAY GRAPHQL — REQUESTS TRANSPORT
#
# IMPORTANT:
#
# There is intentionally NO automatic retry here.
# Railway mutations can create resources.
#
# Read polling happens at higher-level functions only.
# =========================================================

def railway_graphql_requests(
    query,
    variables=None,
    timeout=60
):

    if requests is None:

        raise RuntimeError(
            (
                "Python package 'requests' is missing. "
                "Railway API transport cannot start."
            )
        )

    auth = railway_auth_config()

    token = clean_text(
        auth.get(
            "token"
        ),
        10000
    )

    mode = clean_text(
        auth.get(
            "mode"
        ),
        100
    )

    if not token:

        raise RuntimeError(
            (
                "Railway token is missing. "
                "Expected RAILWAY_API_TOKEN, "
                "RAILWAY_TOKEN, or "
                "RAILWAY_PROJECT_TOKEN."
            )
        )

    headers = {
        "Content-Type":
            "application/json",

        "Accept":
            "application/json"
    }

    if mode == "project":

        headers[
            "Project-Access-Token"
        ] = token

    else:

        headers[
            "Authorization"
        ] = (
            "Bearer "
            +
            token
        )

    payload = {
        "query":
            query,

        "variables":
            variables
            or
            {}
    }

    try:

        response = requests.post(
            RAILWAY_GRAPHQL_URL,
            headers=headers,
            json=payload,
            timeout=timeout
        )

    except requests.RequestException as error:

        raise RuntimeError(
            (
                "Railway network error: "
                +
                clean_text(
                    error,
                    1200
                )
            )
        )

    status = int(
        response.status_code
    )

    # -----------------------------------------------------
    # CLOUDFLARE / ACCESS DENIED
    #
    # Do not retry.
    # -----------------------------------------------------

    if status == 403:

        detail = railway_response_excerpt(
            response,
            2500
        )

        raise RuntimeError(
            (
                "Railway HTTP 403: "
                +
                detail
                +
                " | No automatic retry was made."
            )
        )

    if (
        status
        <
        200
        or
        status
        >=
        300
    ):

        raise RuntimeError(
            (
                "Railway HTTP "
                +
                str(
                    status
                )
                +
                ": "
                +
                railway_response_excerpt(
                    response,
                    2500
                )
            )
        )

    try:

        data = response.json()

    except Exception:

        raise RuntimeError(
            (
                "Railway returned invalid JSON: "
                +
                clean_text(
                    response.text,
                    1500
                )
            )
        )

    if not isinstance(
        data,
        dict
    ):

        raise RuntimeError(
            "Railway returned an invalid GraphQL response."
        )

    errors = data.get(
        "errors"
    )

    if errors:

        messages = railway_graphql_error_messages(
            errors
        )

        if not messages:

            messages = [
                clean_text(
                    errors,
                    2000
                )
            ]

        raise RuntimeError(
            (
                "Railway GraphQL: "
                +
                " | ".join(
                    messages
                )
            )
        )

    result = data.get(
        "data"
    )

    if not isinstance(
        result,
        dict
    ):

        return {}

    return result


# =========================================================
# PROJECT TOKEN SCOPE
# =========================================================

PROJECT_SCOPE_CACHE = None


def railway_project_token_scope():

    global PROJECT_SCOPE_CACHE

    auth = railway_auth_config()

    if auth.get(
        "mode"
    ) != "project":

        return {}

    if isinstance(
        PROJECT_SCOPE_CACHE,
        dict
    ):

        return PROJECT_SCOPE_CACHE

    data = railway_graphql_requests(
        """
        query ProjectTokenScope {
          projectToken {
            projectId
            environmentId
          }
        }
        """
    )

    scope = data.get(
        "projectToken"
    )

    if not isinstance(
        scope,
        dict
    ):

        scope = {}

    PROJECT_SCOPE_CACHE = scope

    return scope


# =========================================================
# RAILWAY PROJECTS
# =========================================================

def railway_list_projects():

    data = railway_graphql_requests(
        """
        query Projects {
          projects {
            edges {
              node {
                id
                name
              }
            }
          }
        }
        """
    )

    edges = (
        (
            data.get(
                "projects"
            )
            or
            {}
        ).get(
            "edges"
        )
        or
        []
    )

    result = []

    for edge in edges:

        node = (
            edge.get(
                "node"
            )
            or
            {}
        )

        if node.get(
            "id"
        ):

            result.append(
                node
            )

    return result


def railway_project_details(
    project_id
):

    data = railway_graphql_requests(
        """
        query Project(
          $id: String!
        ) {
          project(
            id: $id
          ) {
            id
            name

            services {
              edges {
                node {
                  id
                  name
                }
              }
            }

            environments {
              edges {
                node {
                  id
                  name
                }
              }
            }
          }
        }
        """,
        {
            "id":
                project_id
        }
    )

    return data.get(
        "project"
    )


def railway_find_project(
    project_name
):

    wanted = clean_text(
        project_name,
        300
    ).lower()

    auth = railway_auth_config()

    # -----------------------------------------------------
    # PROJECT TOKEN:
    # It cannot list arbitrary projects.
    # Ask Railway which project the token belongs to.
    # -----------------------------------------------------

    if auth.get(
        "mode"
    ) == "project":

        scope = railway_project_token_scope()

        project_id = clean_text(
            scope.get(
                "projectId"
            ),
            300
        )

        if not project_id:

            raise RuntimeError(
                (
                    "Railway project token did not "
                    "return a projectId."
                )
            )

        project = railway_project_details(
            project_id
        )

        if not project:

            return None

        actual_name = clean_text(
            project.get(
                "name"
            ),
            300
        )

        if (
            actual_name.lower()
            !=
            wanted
        ):

            raise RuntimeError(
                (
                    "Railway project token belongs to '"
                    +
                    actual_name
                    +
                    "', not '"
                    +
                    project_name
                    +
                    "'."
                )
            )

        return project

    # -----------------------------------------------------
    # ACCOUNT / WORKSPACE TOKEN
    # -----------------------------------------------------

    for project in railway_list_projects():

        if (
            clean_text(
                project.get(
                    "name"
                ),
                300
            ).lower()
            ==
            wanted
        ):

            return project

    return None


# =========================================================
# ENVIRONMENT
# =========================================================

def railway_production_environment(
    project
):

    edges = (
        (
            project.get(
                "environments"
            )
            or
            {}
        ).get(
            "edges"
        )
        or
        []
    )

    # -----------------------------------------------------
    # Project token is already tied to one environment.
    # Always use that exact Railway environment.
    # -----------------------------------------------------

    auth = railway_auth_config()

    if auth.get(
        "mode"
    ) == "project":

        scope = railway_project_token_scope()

        scoped_environment_id = clean_text(
            scope.get(
                "environmentId"
            ),
            300
        )

        if scoped_environment_id:

            for edge in edges:

                node = (
                    edge.get(
                        "node"
                    )
                    or
                    {}
                )

                if (
                    clean_text(
                        node.get(
                            "id"
                        ),
                        300
                    )
                    ==
                    scoped_environment_id
                ):

                    return node

            return {
                "id":
                    scoped_environment_id,

                "name":
                    "project-token-environment"
            }

    # -----------------------------------------------------
    # Account / Workspace token
    # -----------------------------------------------------

    fallback = None

    for edge in edges:

        node = (
            edge.get(
                "node"
            )
            or
            {}
        )

        if not node.get(
            "id"
        ):

            continue

        if fallback is None:

            fallback = node

        if (
            clean_text(
                node.get(
                    "name"
                )
            ).lower()
            ==
            "production"
        ):

            return node

    if fallback:

        return fallback

    raise RuntimeError(
        "Railway production environment was not found."
    )


# =========================================================
# SERVICE
# =========================================================

def railway_find_service(
    project,
    service_name
):

    wanted = clean_text(
        service_name,
        300
    ).lower()

    edges = (
        (
            project.get(
                "services"
            )
            or
            {}
        ).get(
            "edges"
        )
        or
        []
    )

    for edge in edges:

        node = (
            edge.get(
                "node"
            )
            or
            {}
        )

        if (
            clean_text(
                node.get(
                    "name"
                )
            ).lower()
            ==
            wanted
        ):

            return node

    return None


def railway_create_service(
    project_id,
    service_name
):

    data = railway_graphql_requests(
        """
        mutation ServiceCreate(
          $input: ServiceCreateInput!
        ) {
          serviceCreate(
            input: $input
          ) {
            id
            name
          }
        }
        """,
        {
            "input": {
                "projectId":
                    project_id,

                "name":
                    service_name,

                "source": {
                    "repo":
                        GITHUB_REPO
                }
            }
        }
    )

    service = data.get(
        "serviceCreate"
    )

    if (
        not isinstance(
            service,
            dict
        )
        or
        not service.get(
            "id"
        )
    ):

        raise RuntimeError(
            (
                "Railway did not return "
                "the created service."
            )
        )

    return service


# =========================================================
# SERVICE SETTINGS
# =========================================================

def railway_configure_call_service(
    service_id,
    environment_id
):

    data = railway_graphql_requests(
        """
        mutation ServiceInstanceUpdate(
          $serviceId: String!,
          $environmentId: String!,
          $input: ServiceInstanceUpdateInput!
        ) {
          serviceInstanceUpdate(
            serviceId: $serviceId,
            environmentId: $environmentId,
            input: $input
          )
        }
        """,
        {
            "serviceId":
                service_id,

            "environmentId":
                environment_id,

            "input": {
                "rootDirectory":
                    CALL_ROOT_DIRECTORY,

                "startCommand":
                    CALL_START_COMMAND,

                "healthcheckPath":
                    CALL_HEALTH_PATH,

                "numReplicas":
                    1
            }
        }
    )

    if (
        data.get(
            "serviceInstanceUpdate"
        )
        is not True
    ):

        raise RuntimeError(
            (
                "Railway did not confirm "
                "service configuration."
            )
        )

    return True


# =========================================================
# VARIABLES
# =========================================================

def railway_install_variables(
    project_id,
    environment_id,
    service_id,
    variables
):

    safe_variables = {}

    for key, value in variables.items():

        value = str(
            value
            if value is not None
            else
            ""
        )

        if not value:

            continue

        safe_variables[
            str(
                key
            )
        ] = value

    data = railway_graphql_requests(
        """
        mutation VariableCollectionUpsert(
          $input: VariableCollectionUpsertInput!
        ) {
          variableCollectionUpsert(
            input: $input
          )
        }
        """,
        {
            "input": {
                "projectId":
                    project_id,

                "environmentId":
                    environment_id,

                "serviceId":
                    service_id,

                "variables":
                    safe_variables
            }
        }
    )

    if (
        data.get(
            "variableCollectionUpsert"
        )
        is not True
    ):

        raise RuntimeError(
            (
                "Railway did not confirm "
                "variable installation."
            )
        )

    return True


# =========================================================
# DOMAIN
# =========================================================

def railway_create_domain(
    service_id,
    environment_id
):

    data = railway_graphql_requests(
        """
        mutation ServiceDomainCreate(
          $input: ServiceDomainCreateInput!
        ) {
          serviceDomainCreate(
            input: $input
          ) {
            domain
          }
        }
        """,
        {
            "input": {
                "serviceId":
                    service_id,

                "environmentId":
                    environment_id
            }
        }
    )

    domain = clean_text(
        (
            data.get(
                "serviceDomainCreate"
            )
            or
            {}
        ).get(
            "domain"
        ),
        1000
    )

    if not domain:

        raise RuntimeError(
            "Railway domain was not returned."
        )

    return domain


def railway_existing_domain(
    project_id,
    environment_id,
    service_id
):

    # Reuse the older helper only as a READ operation.
    # Because call_stack.railway_graphql is patched below,
    # even this helper now uses requests.

    try:

        existing = (
            call_stack
            .railway_existing_domain(
                project_id,
                environment_id,
                service_id
            )
        )

        return clean_text(
            existing,
            1000
        )

    except Exception:

        return ""


def railway_resolve_domain(
    registry,
    project_id,
    environment_id,
    service_id
):

    registry_domain = clean_text(
        (
            registry
            or
            {}
        ).get(
            "railway_domain"
        ),
        1000
    )

    if registry_domain:

        return registry_domain

    existing = railway_existing_domain(
        project_id,
        environment_id,
        service_id
    )

    if existing:

        return existing

    # -----------------------------------------------------
    # Create once.
    # No mutation retry.
    # -----------------------------------------------------

    try:

        return railway_create_domain(
            service_id,
            environment_id
        )

    except Exception:

        # If Railway says the domain already exists,
        # perform ONE read check.
        # Do not repeat serviceDomainCreate.

        existing = railway_existing_domain(
            project_id,
            environment_id,
            service_id
        )

        if existing:

            return existing

        raise


# =========================================================
# DEPLOY
# =========================================================

def railway_deploy(
    service_id,
    environment_id
):

    data = railway_graphql_requests(
        """
        mutation ServiceInstanceDeployV2(
          $serviceId: String!,
          $environmentId: String!
        ) {
          serviceInstanceDeployV2(
            serviceId: $serviceId,
            environmentId: $environmentId
          )
        }
        """,
        {
            "serviceId":
                service_id,

            "environmentId":
                environment_id
        }
    )

    deployment_id = clean_text(
        data.get(
            "serviceInstanceDeployV2"
        ),
        300
    )

    if not deployment_id:

        raise RuntimeError(
            (
                "Railway did not return "
                "a deployment ID."
            )
        )

    return deployment_id


def railway_get_deployment(
    deployment_id
):

    data = railway_graphql_requests(
        """
        query Deployment(
          $id: String!
        ) {
          deployment(
            id: $id
          ) {
            id
            status
            createdAt
            updatedAt
          }
        }
        """,
        {
            "id":
                deployment_id
        }
    )

    return data.get(
        "deployment"
    )


def wait_for_deployment(
    deployment_id
):

    deadline = (
        time.time()
        +
        DEPLOY_TIMEOUT_SECONDS
    )

    last_status = ""

    failure_states = {
        "FAILED",
        "CRASHED",
        "CANCELLED",
        "REMOVED"
    }

    while time.time() < deadline:

        deployment = railway_get_deployment(
            deployment_id
        )

        if not isinstance(
            deployment,
            dict
        ):

            time.sleep(
                POLL_SECONDS
            )

            continue

        status = clean_text(
            deployment.get(
                "status"
            ),
            100
        ).upper()

        if (
            status
            and
            status
            !=
            last_status
        ):

            print(
                (
                    "🚆 XPAND CALL DEPLOY | "
                    +
                    deployment_id
                    +
                    " | "
                    +
                    status
                )
            )

            last_status = status

        if status == "SUCCESS":

            return deployment

        if status in failure_states:

            raise RuntimeError(
                (
                    "Railway deployment failed: "
                    +
                    status
                )
            )

        # Deployment status query is READ-ONLY.
        time.sleep(
            POLL_SECONDS
        )

    raise RuntimeError(
        (
            "Railway deployment timed out "
            "before SUCCESS."
        )
    )


# =========================================================
# HTTP HEALTH
# =========================================================

def http_json(
    url,
    timeout=20
):

    if requests is None:

        raise RuntimeError(
            "Python package 'requests' is missing."
        )

    try:

        response = requests.get(
            url,
            headers={
                "Accept":
                    "application/json"
            },
            timeout=timeout
        )

    except requests.RequestException as error:

        raise RuntimeError(
            (
                "HTTP network error: "
                +
                clean_text(
                    error,
                    1000
                )
            )
        )

    status = int(
        response.status_code
    )

    try:

        data = response.json()

    except Exception:

        raise RuntimeError(
            (
                "Health endpoint returned invalid JSON: "
                +
                clean_text(
                    response.text,
                    1200
                )
            )
        )

    return (
        status,
        data
    )


# =========================================================
# OPENAI HEALTH VERIFICATION
# =========================================================

def wait_for_openai_health(
    domain,
    expected_agent_id
):

    domain = clean_text(
        domain,
        1000
    )

    if not domain:

        raise RuntimeError(
            "Railway health domain is missing."
        )

    if (
        domain.startswith(
            "https://"
        )
        or
        domain.startswith(
            "http://"
        )
    ):

        base_url = domain.rstrip(
            "/"
        )

    else:

        base_url = (
            "https://"
            +
            domain.rstrip(
                "/"
            )
        )

    health_url = (
        base_url
        +
        CALL_HEALTH_PATH
    )

    deadline = (
        time.time()
        +
        HEALTH_TIMEOUT_SECONDS
    )

    last_error = ""

    while time.time() < deadline:

        try:

            status, data = http_json(
                health_url,
                timeout=20
            )

            if status != 200:

                raise RuntimeError(
                    (
                        "Health HTTP "
                        +
                        str(
                            status
                        )
                    )
                )

            if not isinstance(
                data,
                dict
            ):

                raise RuntimeError(
                    "Health response is invalid."
                )

            if data.get(
                "ok"
            ) is not True:

                raise RuntimeError(
                    (
                        "Health returned ok=false: "
                        +
                        clean_text(
                            data,
                            1000
                        )
                    )
                )

            returned_agent_id = clean_text(
                data.get(
                    "agentId"
                ),
                200
            ).lower()

            expected_agent_id = clean_text(
                expected_agent_id,
                200
            ).lower()

            if (
                returned_agent_id
                !=
                expected_agent_id
            ):

                raise RuntimeError(
                    (
                        "Health agentId mismatch. "
                        "Expected "
                        +
                        expected_agent_id
                        +
                        ", got "
                        +
                        returned_agent_id
                    )
                )

            if (
                clean_text(
                    data.get(
                        "provider"
                    )
                ).lower()
                !=
                "openai"
            ):

                raise RuntimeError(
                    "Health provider is not OpenAI."
                )

            if (
                clean_text(
                    data.get(
                        "realtimeProvider"
                    )
                ).lower()
                !=
                "openai_realtime"
            ):

                raise RuntimeError(
                    (
                        "Health realtimeProvider "
                        "is not OpenAI Realtime."
                    )
                )

            if (
                clean_text(
                    data.get(
                        "model"
                    )
                )
                !=
                REALTIME_MODEL
            ):

                raise RuntimeError(
                    (
                        "Health realtime model mismatch. "
                        "Expected "
                        +
                        REALTIME_MODEL
                    )
                )

            if (
                clean_text(
                    data.get(
                        "transport"
                    )
                ).lower()
                !=
                "webrtc"
            ):

                raise RuntimeError(
                    "Health transport is not WebRTC."
                )

            if data.get(
                "openaiConfigured"
            ) is not True:

                raise RuntimeError(
                    "OpenAI key is not configured."
                )

            if data.get(
                "databaseConfigured"
            ) is not True:

                raise RuntimeError(
                    "XPAND database is not configured."
                )

            if data.get(
                "telegramConfigured"
            ) is not True:

                raise RuntimeError(
                    "XPAND Telegram token is not configured."
                )

            if data.get(
                "callSecretConfigured"
            ) is not True:

                raise RuntimeError(
                    "XPAND call secret is not configured."
                )

            if data.get(
                "isolatedSecrets"
            ) is not True:

                raise RuntimeError(
                    "Health did not confirm isolated secrets."
                )

            if data.get(
                "kemoPersonalMemory"
            ) is not False:

                raise RuntimeError(
                    (
                        "Health did not confirm "
                        "Kemo memory isolation."
                    )
                )

            if data.get(
                "kemoGeminiReasoning"
            ) is not False:

                raise RuntimeError(
                    (
                        "Health did not confirm "
                        "Gemini live-call isolation."
                    )
                )

            return {
                "url":
                    base_url,

                "healthUrl":
                    health_url,

                "data":
                    data
            }

        except Exception as error:

            last_error = clean_text(
                error,
                1500
            )

        # Health GET is read-only.
        time.sleep(
            POLL_SECONDS
        )

    raise RuntimeError(
        (
            "OpenAI health verification failed: "
            +
            last_error
        )
    )


# =========================================================
# REAL OPENAI CALL VERIFICATION
# =========================================================

def verify_real_openai_call(
    database_url,
    agent_slug
):

    if not database_url:

        return {
            "verified":
                False,

            "reason":
                "XPAND database missing"
        }

    try:

        with call_stack.db_connect(
            database_url
        ) as conn:

            row = call_stack.fetch_one_dict(
                conn,
                """
                SELECT
                    provider,
                    model,
                    transcript,
                    verification,
                    started_at,
                    ended_at

                FROM
                    agent_call_sessions

                WHERE
                    agent_id = %s

                    AND status = 'ended'

                ORDER BY
                    ended_at DESC

                LIMIT 1;
                """,
                (
                    agent_slug,
                )
            )

    except Exception as error:

        return {
            "verified":
                False,

            "reason":
                clean_text(
                    error,
                    1200
                )
        }

    if not row:

        return {
            "verified":
                False,

            "reason":
                "no ended OpenAI call found"
        }

    transcript = parse_json_value(
        row.get(
            "transcript"
        ),
        []
    )

    verification = parse_json_value(
        row.get(
            "verification"
        ),
        {}
    )

    user_turns = [
        item
        for item
        in transcript
        if (
            isinstance(
                item,
                dict
            )
            and
            item.get(
                "role"
            )
            ==
            "user"
            and
            clean_text(
                item.get(
                    "text"
                )
            )
        )
    ]

    assistant_turns = [
        item
        for item
        in transcript
        if (
            isinstance(
                item,
                dict
            )
            and
            item.get(
                "role"
            )
            ==
            "assistant"
            and
            clean_text(
                item.get(
                    "text"
                )
            )
        )
    ]

    provider_ok = (
        clean_text(
            row.get(
                "provider"
            )
        ).lower()
        ==
        "openai"
    )

    model_ok = (
        clean_text(
            row.get(
                "model"
            )
        )
        ==
        REALTIME_MODEL
    )

    evidence_ok = (
        verification.get(
            "realCallCandidate"
        )
        is True
    )

    verified = bool(
        provider_ok
        and
        model_ok
        and
        evidence_ok
        and
        user_turns
        and
        assistant_turns
    )

    return {
        "verified":
            verified,

        "provider":
            clean_text(
                row.get(
                    "provider"
                )
            ),

        "model":
            clean_text(
                row.get(
                    "model"
                )
            ),

        "userTurns":
            len(
                user_turns
            ),

        "assistantTurns":
            len(
                assistant_turns
            ),

        "realCallCandidate":
            evidence_ok,

        "webrtcConnected":
            verification.get(
                "webrtcConnected"
            )
            is True,

        "openaiSessionCreated":
            verification.get(
                "openaiSessionCreated"
            )
            is True,

        "userAudioReceived":
            verification.get(
                "userAudioReceived"
            )
            is True,

        "assistantAudioReceived":
            verification.get(
                "assistantAudioReceived"
            )
            is True,

        "assistantAudioPlayed":
            verification.get(
                "assistantAudioPlayed"
            )
            is True,

        "endedAt":
            str(
                row.get(
                    "ended_at"
                )
                or
                ""
            ),

        "reason":
            (
                "real OpenAI two-way call verified"
                if verified
                else
                (
                    "real OpenAI two-way evidence "
                    "is not complete yet"
                )
            )
    }


# =========================================================
# INSTALL OPENAI LIVE CALL
# =========================================================

def install_openai_live_call(
    owner_user_id,
    resolved
):

    profile = (
        resolved.get(
            "profile"
        )
        or
        {}
    )

    agent_row = resolved.get(
        "row"
    )

    agent_slug = clean_text(
        profile.get(
            "slug"
        )
        or
        "xpand",
        100
    ).lower()

    agent_name = clean_text(
        profile.get(
            "name"
        )
        or
        "XPAND Agent",
        300
    )

    bot_username = clean_text(
        profile.get(
            "username"
        ),
        300
    )

    system_prompt = clean_text(
        profile.get(
            "prompt"
        ),
        60000
    )

    # -----------------------------------------------------
    # Current V2 scope
    # -----------------------------------------------------

    if agent_slug != "xpand":

        raise RuntimeError(
            (
                "OpenAI Live Call V2.2 is currently "
                "approved only for XPAND."
            )
        )

    # -----------------------------------------------------
    # AI provider policy
    # -----------------------------------------------------

    ai_policy.require_xpand_openai_policy(
        "live_call"
    )

    # -----------------------------------------------------
    # Requirements
    # -----------------------------------------------------

    missing = []

    if requests is None:

        missing.append(
            "Python package: requests"
        )

    if not railway_token_ready():

        missing.append(
            (
                "RAILWAY_API_TOKEN "
                "or RAILWAY_PROJECT_TOKEN"
            )
        )

    if not xpand_openai_key():

        missing.append(
            "XPAND_OPENAI_API_KEY"
        )

    if not xpand_database_url():

        missing.append(
            "XPAND_DATABASE_URL"
        )

    if not system_prompt:

        missing.append(
            "agents/xpand/system_prompt.md"
        )

    if missing:

        return {
            "blocked":
                True,

            "agentSlug":
                agent_slug,

            "agentName":
                agent_name,

            "missing":
                missing
        }

    try:

        # =================================================
        # TELEGRAM MANAGED BOT TOKEN
        # =================================================

        managed_bot = (
            call_stack
            .fetch_managed_bot_token(
                agent_row
            )
        )

        if managed_bot.get(
            "username"
        ):

            bot_username = clean_text(
                managed_bot.get(
                    "username"
                ),
                300
            )

        # =================================================
        # REGISTRY
        # =================================================

        call_stack.init_call_registry()

        registry = (
            call_stack.get_call_registry(
                owner_user_id,
                agent_slug
            )
            or
            {}
        )

        # Already genuinely verified.
        if (
            clean_text(
                registry.get(
                    "status"
                )
            ).lower()
            ==
            "verified"
        ):

            return {
                "ok":
                    True,

                "alreadyVerified":
                    True,

                "agentSlug":
                    agent_slug,

                "agentName":
                    agent_name,

                "url":
                    clean_text(
                        registry.get(
                            "railway_domain"
                        ),
                        1000
                    ),

                "status":
                    "verified"
            }

        call_stack.update_call_registry(
            owner_user_id,
            agent_slug,

            agent_name=
                agent_name,

            bot_username=
                bot_username,

            agent_db_id=
                (
                    call_stack.agent_db_id(
                        agent_row
                    )
                    if agent_row
                    else
                    ""
                ),

            status=
                "openai_provisioning",

            last_error=
                None
        )

        print(
            (
                "📞 OPENAI CALL PROVISION | "
                +
                agent_name
                +
                " | STARTED"
            )
        )

        # =================================================
        # PROJECT
        # =================================================

        project = railway_find_project(
            "xpand-agent"
        )

        if not project:

            raise RuntimeError(
                (
                    "Railway project xpand-agent "
                    "was not found. "
                    "No duplicate project was created."
                )
            )

        project_id = clean_text(
            project.get(
                "id"
            ),
            300
        )

        if not project_id:

            raise RuntimeError(
                "xpand-agent Railway project ID missing."
            )

        # Refresh full details.
        project = railway_project_details(
            project_id
        )

        if not project:

            raise RuntimeError(
                "Could not load xpand-agent project."
            )

        call_stack.update_call_registry(
            owner_user_id,
            agent_slug,

            railway_project_id=
                project_id,

            status=
                "project_verified"
        )

        # =================================================
        # ENVIRONMENT
        # =================================================

        environment = railway_production_environment(
            project
        )

        environment_id = clean_text(
            environment.get(
                "id"
            ),
            300
        )

        if not environment_id:

            raise RuntimeError(
                "Railway environment ID missing."
            )

        call_stack.update_call_registry(
            owner_user_id,
            agent_slug,

            railway_environment_id=
                environment_id,

            status=
                "environment_verified"
        )

        # =================================================
        # SERVICE
        # =================================================

        service = railway_find_service(
            project,
            "xpand-call"
        )

        if not service:

            service = railway_create_service(
                project_id,
                "xpand-call"
            )

            # Railway needs a brief moment to create
            # the production service instance.
            time.sleep(
                3
            )

        service_id = clean_text(
            service.get(
                "id"
            ),
            300
        )

        if not service_id:

            raise RuntimeError(
                "xpand-call service ID missing."
            )

        call_stack.update_call_registry(
            owner_user_id,
            agent_slug,

            railway_service_id=
                service_id,

            status=
                "service_verified"
        )

        # =================================================
        # SERVICE CONFIGURATION
        # =================================================

        railway_configure_call_service(
            service_id,
            environment_id
        )

        call_stack.update_call_registry(
            owner_user_id,
            agent_slug,

            status=
                "service_configured"
        )

        # =================================================
        # CALL SECRET
        # =================================================

        call_secret = secrets.token_urlsafe(
            48
        )

        # =================================================
        # XPAND-ISOLATED VARIABLES
        # =================================================

        variables = {
            "AGENT_ID":
                "xpand",

            "AGENT_NAME":
                agent_name,

            "AGENT_SECRET_PREFIX":
                "XPAND",

            "XPAND_OPENAI_API_KEY":
                xpand_openai_key(),

            "XPAND_DATABASE_URL":
                xpand_database_url(),

            "XPAND_TELEGRAM_BOT_TOKEN":
                managed_bot[
                    "token"
                ],

            "XPAND_TELEGRAM_ALLOWED_USER_ID":
                str(
                    int(
                        owner_user_id
                    )
                ),

            "XPAND_CALL_SECRET":
                call_secret,

            "XPAND_SYSTEM_PROMPT":
                system_prompt,

            "XPAND_REALTIME_MODEL":
                REALTIME_MODEL,

            "XPAND_TRANSCRIBE_MODEL":
                TRANSCRIBE_MODEL,

            "XPAND_VOICE":
                REALTIME_VOICE,

            "XPAND_TIMEZONE":
                TIMEZONE,

            "XPAND_CALL_CONTINUITY_MINUTES":
                "15"
        }

        railway_install_variables(
            project_id,
            environment_id,
            service_id,
            variables
        )

        call_stack.update_call_registry(
            owner_user_id,
            agent_slug,

            status=
                "openai_variables_configured"
        )

        # =================================================
        # DOMAIN
        # =================================================

        domain = railway_resolve_domain(
            registry,
            project_id,
            environment_id,
            service_id
        )

        call_stack.update_call_registry(
            owner_user_id,
            agent_slug,

            railway_domain=
                domain,

            status=
                "domain_ready"
        )

        # =================================================
        # DEPLOY
        # =================================================

        deployment_id = railway_deploy(
            service_id,
            environment_id
        )

        call_stack.update_call_registry(
            owner_user_id,
            agent_slug,

            railway_deployment_id=
                deployment_id,

            status=
                "deploying_openai_realtime"
        )

        deployment = wait_for_deployment(
            deployment_id
        )

        call_stack.update_call_registry(
            owner_user_id,
            agent_slug,

            status=
                "deployment_success"
        )

        # =================================================
        # HEALTH
        # =================================================

        health = wait_for_openai_health(
            domain,
            agent_slug
        )

        call_stack.update_call_registry(
            owner_user_id,
            agent_slug,

            status=
                "openai_health_verified",

            health_json=
                health[
                    "data"
                ],

            last_error=
                None
        )

        # =================================================
        # TELEGRAM CALL BUTTON
        # =================================================

        call_stack.configure_child_call_button(
            managed_bot[
                "token"
            ],
            owner_user_id,
            agent_name,
            health[
                "url"
            ]
        )

        # =================================================
        # READY FOR REAL TEST
        # =================================================

        call_stack.update_call_registry(
            owner_user_id,
            agent_slug,

            status=
                "ready_for_real_test",

            last_error=
                None
        )

        call_stack.try_sync_capability(
            agent_row,

            status=
                "ready_for_real_test",

            verified=
                False,

            config={
                "provider":
                    "openai",

                "realtimeProvider":
                    "openai_realtime",

                "model":
                    REALTIME_MODEL,

                "transport":
                    "webrtc",

                "url":
                    health[
                        "url"
                    ],

                "railwayProjectId":
                    project_id,

                "railwayEnvironmentId":
                    environment_id,

                "railwayServiceId":
                    service_id,

                "deploymentId":
                    deployment_id,

                "isolatedSecrets":
                    True,

                "kemoMemory":
                    False,

                "geminiLiveCallReasoning":
                    False
            }
        )

        print(
            (
                "✅ OPENAI LIVE CALL READY | "
                +
                agent_name
                +
                " | "
                +
                health[
                    "url"
                ]
            )
        )

        return {
            "ok":
                True,

            "alreadyVerified":
                False,

            "agentSlug":
                agent_slug,

            "agentName":
                agent_name,

            "botUsername":
                bot_username,

            "projectId":
                project_id,

            "environmentId":
                environment_id,

            "serviceId":
                service_id,

            "deploymentId":
                deployment_id,

            "deploymentStatus":
                deployment.get(
                    "status"
                ),

            "url":
                health[
                    "url"
                ],

            "health":
                health[
                    "data"
                ],

            "provider":
                "openai",

            "model":
                REALTIME_MODEL,

            "status":
                "ready_for_real_test"
        }

    except Exception as error:

        # Record failure without pretending success.
        try:

            call_stack.update_call_registry(
                owner_user_id,
                agent_slug,

                status=
                    "provisioning_failed",

                last_error=
                    clean_text(
                        error,
                        4000
                    )
            )

        except Exception:
            pass

        print(
            (
                "❌ XPAND OPENAI CALL PROVISION | "
                +
                clean_text(
                    error,
                    3000
                )
            )
        )

        raise


# =========================================================
# VERIFY OPENAI LIVE CALL
# =========================================================

def verify_openai_live_call(
    owner_user_id,
    resolved
):

    profile = (
        resolved.get(
            "profile"
        )
        or
        {}
    )

    agent_row = resolved.get(
        "row"
    )

    agent_slug = clean_text(
        profile.get(
            "slug"
        )
        or
        "xpand",
        100
    ).lower()

    agent_name = clean_text(
        profile.get(
            "name"
        )
        or
        "XPAND Agent",
        300
    )

    call_stack.init_call_registry()

    registry = call_stack.get_call_registry(
        owner_user_id,
        agent_slug
    )

    if not registry:

        return {
            "installed":
                False,

            "verified":
                False,

            "agentName":
                agent_name
        }

    result = verify_real_openai_call(
        xpand_database_url(),
        agent_slug
    )

    if result.get(
        "verified"
    ):

        call_stack.update_call_registry(
            owner_user_id,
            agent_slug,

            status=
                "verified",

            verified_at=
                now_utc(),

            last_error=
                None
        )

        call_stack.try_sync_capability(
            agent_row,

            status=
                "verified",

            verified=
                True,

            config={
                "provider":
                    "openai",

                "realtimeProvider":
                    "openai_realtime",

                "model":
                    REALTIME_MODEL,

                "transport":
                    "webrtc",

                "realCall":
                    result
            }
        )

        print(
            (
                "✅ XPAND OPENAI LIVE CALL VERIFIED | "
                +
                REALTIME_MODEL
            )
        )

    return {
        "installed":
            True,

        "verified":
            bool(
                result.get(
                    "verified"
                )
            ),

        "agentName":
            agent_name,

        "registry":
            registry,

        "realCall":
            result
    }


# =========================================================
# NATURAL LANGUAGE ALIASES
# =========================================================

EXTRA_CALL_MARKERS = [
    "ميزة المكالمة",
    "ميزة الاتصال",
    "المكالمة المباشرة",
    "مكالمة مباشرة",
    "اتصال مباشر",
    "اتصال صوتي مباشر",
    "محادثة صوتية مباشرة",
    "محادثة مباشرة",
    "ميزة المحادثة",
    "ميزة الدردشة",
    "دردشة صوتية",
    "live call",
    "realtime call",
    "voice call",
    "webrtc"
]


def install_natural_call_aliases():

    existing = getattr(
        call_stack,
        "CALL_MARKERS",
        []
    )

    if not isinstance(
        existing,
        list
    ):

        existing = list(
            existing
            or
            []
        )

    for marker in EXTRA_CALL_MARKERS:

        if marker not in existing:

            existing.append(
                marker
            )

    call_stack.CALL_MARKERS = existing

    return True


# =========================================================
# PATCH EXISTING STACK
#
# Critical part of V2.2:
#
# Every old helper that calls:
#
#     call_stack.railway_graphql(...)
#
# now reaches railway_graphql_requests().
#
# We do NOT need to rewrite the old giant V1 file.
# =========================================================

def install_openai_call_patch():

    # Railway HTTP transport.
    call_stack.railway_graphql = (
        railway_graphql_requests
    )

    # Compatibility for bool/token checks.
    call_stack.railway_token = (
        railway_token_compat
    )

    # OpenAI live-call implementation.
    call_stack.install_live_call = (
        install_openai_live_call
    )

    call_stack.verify_live_call = (
        verify_openai_live_call
    )

    # Natural Arabic command aliases.
    install_natural_call_aliases()

    return True


# =========================================================
# STARTUP STATUS
# =========================================================

def startup_status():

    try:

        policy_result = (
            ai_policy
            .require_xpand_openai_policy(
                "live_call"
            )
        )

        policy_ready = bool(
            policy_result.get(
                "ok"
            )
        )

    except Exception:

        policy_ready = False

    auth = railway_auth_config()

    return {
        "requests":
            requests is not None,

        "railway":
            railway_token_ready(),

        "railwayAuth":
            clean_text(
                auth.get(
                    "mode"
                ),
                100
            )
            or
            "missing",

        "openai":
            bool(
                xpand_openai_key()
            ),

        "database":
            bool(
                xpand_database_url()
            ),

        "policy":
            policy_ready,

        "model":
            REALTIME_MODEL,

        "transcribe":
            TRANSCRIBE_MODEL
    }


# =========================================================
# MAIN
# =========================================================

def main():

    # Install patch BEFORE any Railway provisioning.
    install_openai_call_patch()

    # Preserve XPAND OpenAI policy.
    validation = (
        ai_policy
        .install_ai_policy()
    )

    call_stack.init_call_registry()

    status = startup_status()

    print("")
    print(
        "================================================"
    )
    print(
        " XPAND AGENT FACTORY OPENAI CALL V2.2"
    )
    print(
        " XPAND REALTIME / WEBRTC PROVISIONER"
    )
    print(
        "================================================"
    )
    print("")

    print(
        (
            "✅ Railway HTTP client: "
            +
            (
                "REQUESTS READY"
                if status[
                    "requests"
                ]
                else
                "REQUESTS MISSING"
            )
        )
    )

    print(
        (
            "✅ Railway Factory Token: "
            +
            (
                "READY"
                if status[
                    "railway"
                ]
                else
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ Railway Auth Mode: "
            +
            status[
                "railwayAuth"
            ].upper()
        )
    )

    print(
        (
            "✅ XPAND OpenAI Key: "
            +
            (
                "READY"
                if status[
                    "openai"
                ]
                else
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ XPAND Database: "
            +
            (
                "READY"
                if status[
                    "database"
                ]
                else
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ XPAND AI Policy: "
            +
            (
                "OPENAI ENFORCED"
                if status[
                    "policy"
                ]
                else
                "INVALID"
            )
        )
    )

    print(
        (
            "✅ Realtime model: "
            +
            status[
                "model"
            ]
        )
    )

    print(
        (
            "✅ Transcription model: "
            +
            status[
                "transcribe"
            ]
        )
    )

    print(
        "✅ Transport: WEBRTC"
    )

    print(
        "✅ Railway GraphQL transport: REQUESTS"
    )

    print(
        "🚫 Railway mutations: NO AUTO RETRY"
    )

    print(
        "✅ Target Railway project: xpand-agent"
    )

    print(
        "✅ Target Railway service: xpand-call"
    )

    print(
        "🔒 XPAND OpenAI key isolated"
    )

    print(
        "🔒 XPAND Database isolated"
    )

    print(
        "🔒 XPAND Telegram token isolated"
    )

    print(
        "🔒 Kemo Gemini runtime unchanged"
    )

    print(
        "🚫 Gemini live-call reasoning blocked"
    )

    print(
        "🚫 No VERIFIED status before real call"
    )

    print("")

    print(
        "✅ OPENAI LIVE CALL PROVISIONER ONLINE"
    )

    print("")

    if not validation.get(
        "ok"
    ):

        print(
            "⚠️ XPAND AI policy contains errors."
        )

    # Start the already-existing lower Agent Factory stack.
    #
    # We intentionally do not call call_stack.main()
    # because that prints the old Gemini live-call
    # provisioner information.

    profiles.main()


# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":

    main()
