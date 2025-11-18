"""
Infrastructure Security Penetration Tests
Tests for Docker, Redis, PostgreSQL, and deployment security

CRITICAL INFRASTRUCTURE ISSUES:
1. Redis without authentication
2. PostgreSQL default credentials
3. Docker container escape risks
4. Secrets in environment variables
5. Missing network isolation
"""

import pytest
import redis
import psycopg2
import docker
import os
import subprocess
from typing import List, Dict, Any


class TestRedisSecurityPenetration:
    """Redis security penetration tests"""

    @pytest.mark.critical
    def test_redis_anonymous_access(self):
        """
        CRITICAL: Redis allows anonymous access

        LOCATION: docker/docker-compose.yml:31
        ISSUE: Password in command but not enforced by client code
        """
        try:
            # Attempt connection WITHOUT password
            r = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True
            )

            # Try to read data
            result = r.ping()

            if result:
                pytest.fail(
                    "CRITICAL: Redis accessible without authentication!\n"
                    "FIX 1: Update src/api/main.py:101-110 to include password\n"
                    "FIX 2: Enforce requirepass in Redis configuration"
                )

        except redis.AuthenticationError:
            print("SECURE: Redis requires authentication")
        except redis.ConnectionError:
            pytest.skip("Redis not running")

    @pytest.mark.critical
    def test_redis_dangerous_commands(self):
        """
        Test if dangerous Redis commands are disabled
        """
        dangerous_commands = {
            "FLUSHALL": "Delete all data",
            "FLUSHDB": "Delete current database",
            "CONFIG": "Modify configuration",
            "SHUTDOWN": "Stop Redis server",
            "DEBUG": "Debug commands",
            "SCRIPT": "Execute Lua scripts",
            "EVAL": "Execute Lua code",
        }

        try:
            r = redis.Redis(host='localhost', port=6379)

            for cmd, description in dangerous_commands.items():
                try:
                    if cmd == "CONFIG":
                        r.execute_command("CONFIG", "GET", "*")
                    elif cmd == "SCRIPT":
                        r.execute_command("SCRIPT", "LOAD", "return 1")
                    elif cmd == "EVAL":
                        r.eval("return 1", 0)
                    else:
                        r.execute_command(cmd)

                    pytest.fail(
                        f"CRITICAL: Dangerous Redis command '{cmd}' is enabled!\n"
                        f"Risk: {description}\n"
                        "FIX: Disable dangerous commands in redis.conf:\n"
                        f"rename-command {cmd} \"\""
                    )

                except redis.ResponseError as e:
                    # Command disabled or requires auth - GOOD!
                    print(f"SECURE: {cmd} command properly restricted")

        except redis.ConnectionError:
            pytest.skip("Redis not running")

    def test_redis_cache_poisoning(self):
        """
        Test Redis cache poisoning attack
        """
        try:
            r = redis.Redis(
                host='localhost',
                port=6379,
                password=os.getenv('REDIS_PASSWORD')
            )

            # Attempt to poison cache with malicious data
            malicious_payloads = [
                ("user:admin:role", "superadmin"),
                ("cache:sql_injection", "' OR '1'='1"),
                ("session:attack", "<script>alert('XSS')</script>"),
            ]

            for key, value in malicious_payloads:
                try:
                    r.set(key, value)

                    # If successful, verify it can be retrieved
                    retrieved = r.get(key)

                    if retrieved == value:
                        print(f"WARNING: Cache poisoning possible with key: {key}")

                    # Cleanup
                    r.delete(key)

                except Exception as e:
                    print(f"Cache poisoning blocked: {e}")

        except redis.ConnectionError:
            pytest.skip("Redis not running")


class TestPostgreSQLSecurityPenetration:
    """PostgreSQL security penetration tests"""

    @pytest.mark.critical
    def test_postgres_default_credentials(self):
        """
        CRITICAL: PostgreSQL may use default/weak credentials

        LOCATION: docker/docker-compose.yml:8-12
        ISSUE: Default credentials in environment
        """
        # Attempt connection with default credentials
        default_credentials = [
            ("secuser", "secpass"),     # From docker-compose.yml
            ("postgres", "postgres"),    # Common default
            ("admin", "admin"),
            ("root", "root"),
        ]

        for username, password in default_credentials:
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="sec_latent",
                    user=username,
                    password=password
                )

                if username in ["postgres", "admin", "root"] or password in ["admin", "root", "secpass"]:
                    pytest.fail(
                        f"CRITICAL: PostgreSQL accessible with weak credentials!\n"
                        f"Username: {username}, Password: {password}\n"
                        "FIX: Use strong passwords from secrets manager"
                    )

                conn.close()

            except psycopg2.OperationalError:
                # Connection failed - credentials rejected (GOOD) or DB not running
                pass

    def test_postgres_privilege_escalation(self):
        """
        Test PostgreSQL privilege escalation vulnerabilities
        """
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="sec_latent",
                user=os.getenv("POSTGRES_USER", "secuser"),
                password=os.getenv("POSTGRES_PASSWORD", "secpass")
            )

            cursor = conn.cursor()

            # Test if user can create databases (should be restricted)
            try:
                cursor.execute("CREATE DATABASE test_attack_db;")

                print("WARNING: User can create databases - may be over-privileged")

                # Cleanup
                cursor.execute("DROP DATABASE test_attack_db;")

            except psycopg2.Error:
                print("SECURE: User cannot create databases")

            # Test if user can create extensions (potential code execution)
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
                print("WARNING: User can create extensions")
            except psycopg2.Error:
                print("SECURE: User cannot create extensions")

            cursor.close()
            conn.close()

        except psycopg2.OperationalError:
            pytest.skip("PostgreSQL not available")

    def test_postgres_sql_injection_through_connection(self):
        """
        Test SQL injection through connection parameters
        """
        # Malicious database names
        malicious_db_names = [
            "sec_latent'; DROP TABLE users--",
            "sec_latent' OR '1'='1",
        ]

        for db_name in malicious_db_names:
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database=db_name,
                    user=os.getenv("POSTGRES_USER", "secuser"),
                    password=os.getenv("POSTGRES_PASSWORD", "secpass")
                )

                # Should not connect to malicious database name
                pytest.fail(f"SQL injection possible with database: {db_name}")

                conn.close()

            except psycopg2.Error:
                # Connection failed - injection blocked (GOOD)
                pass


class TestDockerSecurityPenetration:
    """Docker container security tests"""

    def test_docker_container_escape(self):
        """
        Test Docker container escape vulnerabilities
        """
        try:
            client = docker.from_env()

            # Check for privileged containers
            containers = client.containers.list()

            for container in containers:
                # Check if container is privileged
                inspect = client.api.inspect_container(container.id)

                is_privileged = inspect.get('HostConfig', {}).get('Privileged', False)

                if is_privileged:
                    pytest.fail(
                        f"CRITICAL: Container {container.name} is running in privileged mode!\n"
                        "RISK: Container escape possible\n"
                        "FIX: Remove privileged: true from docker-compose.yml"
                    )

        except docker.errors.DockerException:
            pytest.skip("Docker not available")

    def test_docker_secrets_exposure(self):
        """
        Test if secrets are exposed in Docker environment
        """
        try:
            client = docker.from_env()
            containers = client.containers.list()

            sensitive_env_vars = [
                "PASSWORD",
                "SECRET",
                "API_KEY",
                "TOKEN",
                "PRIVATE_KEY",
            ]

            for container in containers:
                inspect = client.api.inspect_container(container.id)
                env_vars = inspect.get('Config', {}).get('Env', [])

                for env in env_vars:
                    for sensitive in sensitive_env_vars:
                        if sensitive in env.upper():
                            print(
                                f"WARNING: Container {container.name} has sensitive "
                                f"environment variable: {env.split('=')[0]}"
                            )

        except docker.errors.DockerException:
            pytest.skip("Docker not available")

    def test_docker_network_isolation(self):
        """
        Test Docker network isolation
        """
        try:
            client = docker.from_env()
            networks = client.networks.list()

            for network in networks:
                # Check if network is in host mode (no isolation)
                if network.attrs.get('Driver') == 'host':
                    print(
                        f"WARNING: Network {network.name} uses host driver - "
                        "no network isolation"
                    )

        except docker.errors.DockerException:
            pytest.skip("Docker not available")


class TestSecretsManagementPenetration:
    """Secrets management security tests"""

    def test_secrets_in_code(self):
        """
        Test for hardcoded secrets in codebase
        """
        secret_patterns = [
            "password",
            "secret_key",
            "api_key",
            "private_key",
            "token",
            "credentials",
        ]

        # Check configuration files
        config_files = [
            "config/settings.py",
            "config/security_config.py",
            ".env.example",
        ]

        found_secrets = []

        for config_file in config_files:
            file_path = os.path.join(
                "/mnt/c/Users/brand/Development/Project_Workspace/active-development/sec_latent",
                config_file
            )

            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read().lower()

                    for pattern in secret_patterns:
                        if f"{pattern} =" in content or f'{pattern}=' in content:
                            # Check if it's a hardcoded value (not env var)
                            if "os.environ" not in content and "os.getenv" not in content:
                                found_secrets.append(f"{config_file}: {pattern}")

        if found_secrets:
            print(f"WARNING: Potential hardcoded secrets found:\n" + "\n".join(found_secrets))

    def test_secrets_in_environment(self):
        """
        Test for secrets in environment variables
        """
        sensitive_patterns = [
            "JWT_SECRET",
            "API_KEY_SECRET",
            "POSTGRES_PASSWORD",
            "REDIS_PASSWORD",
        ]

        exposed_secrets = []

        for pattern in sensitive_patterns:
            value = os.getenv(pattern)

            if value:
                # Check if it's a default/weak value
                weak_values = ["secret", "password", "changeme", "admin", "test"]

                if any(weak in value.lower() for weak in weak_values):
                    exposed_secrets.append(f"{pattern} has weak value")

        if exposed_secrets:
            print("WARNING: Weak secrets in environment:\n" + "\n".join(exposed_secrets))


class TestKubernetesSecurityPenetration:
    """Kubernetes deployment security tests"""

    def test_k8s_secrets_exposure(self):
        """
        Test Kubernetes secrets exposure
        """
        k8s_dir = "/mnt/c/Users/brand/Development/Project_Workspace/active-development/sec_latent/k8s"

        if not os.path.exists(k8s_dir):
            pytest.skip("Kubernetes configs not found")

        # Check for hardcoded secrets in K8s manifests
        for root, dirs, files in os.walk(k8s_dir):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    file_path = os.path.join(root, file)

                    with open(file_path, 'r') as f:
                        content = f.read()

                        # Check for hardcoded passwords/secrets
                        if 'password:' in content.lower() and 'secretKeyRef' not in content:
                            print(f"WARNING: Potential hardcoded secret in {file}")

    def test_k8s_security_context(self):
        """
        Test Kubernetes pod security context
        """
        # This would require kubectl access
        # Document security context requirements

        required_security_contexts = {
            "runAsNonRoot": True,
            "readOnlyRootFilesystem": True,
            "allowPrivilegeEscalation": False,
        }

        print("Required Kubernetes security contexts:")
        for key, value in required_security_contexts.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
