"""
O Construtor - GitHub Client
Cliente para integração com GitHub API

Gerencia:
- Pull Requests (criar, revisar, comentar)
- Issues (criar, responder, fechar)
- Branches e commits
- Code review automatizado
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PRStatus(Enum):
    """Status de um Pull Request"""
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class ReviewDecision(Enum):
    """Decisão de review"""
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    COMMENT = "COMMENT"


@dataclass
class PullRequest:
    """Dados de um Pull Request"""
    number: int
    title: str
    description: str
    author: str
    branch: str
    base_branch: str
    status: PRStatus
    files_changed: List[str] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    url: str = ""


@dataclass
class Issue:
    """Dados de uma Issue"""
    number: int
    title: str
    body: str
    author: str
    labels: List[str] = field(default_factory=list)
    status: str = "open"
    created_at: Optional[datetime] = None
    url: str = ""


class GitHubClient:
    """
    Cliente para GitHub API

    Integra O Construtor com GitHub para:
    - Automação de code review
    - Resposta a issues
    - Criação de PRs
    - Gerenciamento de branches

    Uso:
        client = GitHubClient(repo="owner/repo")
        await client.initialize()

        # Obter PR
        pr = await client.get_pull_request(123)

        # Postar review
        await client.post_review(
            pr_number=123,
            body="LGTM!",
            decision=ReviewDecision.APPROVE,
        )
    """

    def __init__(
        self,
        repo: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.repo = repo or os.getenv("GITHUB_REPOSITORY")
        self.token = token or os.getenv("GITHUB_TOKEN")

        self._github: Optional[Any] = None
        self._repo_obj: Optional[Any] = None
        self._initialized = False

        logger.info(f"GitHubClient initialized for {self.repo}")

    async def initialize(self) -> bool:
        """Inicializa cliente GitHub"""
        if self._initialized:
            return True

        try:
            from github import Github

            self._github = Github(self.token)
            if self.repo:
                self._repo_obj = self._github.get_repo(self.repo)

            self._initialized = True
            logger.info("GitHub client initialized")
            return True

        except Exception as e:
            logger.error(f"GitHub initialization failed: {e}")
            return False

    # ============================================================
    # PULL REQUESTS
    # ============================================================

    async def get_pull_request(self, pr_number: int) -> Optional[PullRequest]:
        """
        Obtém dados de um Pull Request.

        Args:
            pr_number: Número do PR

        Returns:
            PullRequest ou None
        """
        await self.initialize()

        if not self._repo_obj:
            return None

        try:
            pr = self._repo_obj.get_pull(pr_number)

            files = list(pr.get_files())
            files_changed = [f.filename for f in files]

            return PullRequest(
                number=pr.number,
                title=pr.title,
                description=pr.body or "",
                author=pr.user.login,
                branch=pr.head.ref,
                base_branch=pr.base.ref,
                status=PRStatus.MERGED if pr.merged else PRStatus.OPEN if pr.state == "open" else PRStatus.CLOSED,
                files_changed=files_changed,
                additions=pr.additions,
                deletions=pr.deletions,
                created_at=pr.created_at,
                updated_at=pr.updated_at,
                url=pr.html_url,
            )

        except Exception as e:
            logger.error(f"Failed to get PR {pr_number}: {e}")
            return None

    async def get_pr_files(
        self,
        pr_number: int,
        extensions: Optional[List[str]] = None,
        max_files: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Obtém arquivos modificados em um PR.

        Args:
            pr_number: Número do PR
            extensions: Filtrar por extensões
            max_files: Máximo de arquivos

        Returns:
            Lista de arquivos com patches
        """
        await self.initialize()

        if not self._repo_obj:
            return []

        try:
            pr = self._repo_obj.get_pull(pr_number)
            files = []

            for file in pr.get_files():
                # Filtro de extensão
                if extensions:
                    ext = "." + file.filename.split(".")[-1] if "." in file.filename else ""
                    if ext not in extensions:
                        continue

                files.append({
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "patch": file.patch or "",
                })

                if len(files) >= max_files:
                    break

            return files

        except Exception as e:
            logger.error(f"Failed to get PR files: {e}")
            return []

    async def post_review(
        self,
        pr_number: int,
        body: str,
        decision: ReviewDecision = ReviewDecision.COMMENT,
    ) -> bool:
        """
        Posta review em um PR.

        Args:
            pr_number: Número do PR
            body: Conteúdo do review
            decision: Decisão (approve, request_changes, comment)

        Returns:
            True se sucesso
        """
        await self.initialize()

        if not self._repo_obj:
            return False

        try:
            pr = self._repo_obj.get_pull(pr_number)
            pr.create_review(body=body, event=decision.value)

            logger.info(f"Review posted to PR #{pr_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to post review: {e}")
            return False

    async def post_comment(
        self,
        pr_number: int,
        body: str,
    ) -> bool:
        """
        Posta comentário em um PR.

        Args:
            pr_number: Número do PR
            body: Conteúdo do comentário

        Returns:
            True se sucesso
        """
        await self.initialize()

        if not self._repo_obj:
            return False

        try:
            pr = self._repo_obj.get_pull(pr_number)
            pr.create_issue_comment(body)

            logger.info(f"Comment posted to PR #{pr_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to post comment: {e}")
            return False

    async def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> Optional[PullRequest]:
        """
        Cria um novo Pull Request.

        Args:
            title: Título do PR
            body: Descrição
            head: Branch source
            base: Branch target

        Returns:
            PullRequest criado
        """
        await self.initialize()

        if not self._repo_obj:
            return None

        try:
            pr = self._repo_obj.create_pull(
                title=title,
                body=body,
                head=head,
                base=base,
            )

            return PullRequest(
                number=pr.number,
                title=pr.title,
                description=pr.body or "",
                author=pr.user.login,
                branch=head,
                base_branch=base,
                status=PRStatus.OPEN,
                url=pr.html_url,
            )

        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            return None

    # ============================================================
    # ISSUES
    # ============================================================

    async def get_issue(self, issue_number: int) -> Optional[Issue]:
        """
        Obtém dados de uma Issue.

        Args:
            issue_number: Número da issue

        Returns:
            Issue ou None
        """
        await self.initialize()

        if not self._repo_obj:
            return None

        try:
            issue = self._repo_obj.get_issue(issue_number)

            return Issue(
                number=issue.number,
                title=issue.title,
                body=issue.body or "",
                author=issue.user.login,
                labels=[l.name for l in issue.labels],
                status=issue.state,
                created_at=issue.created_at,
                url=issue.html_url,
            )

        except Exception as e:
            logger.error(f"Failed to get issue {issue_number}: {e}")
            return None

    async def post_issue_comment(
        self,
        issue_number: int,
        body: str,
    ) -> bool:
        """
        Posta comentário em uma Issue.

        Args:
            issue_number: Número da issue
            body: Conteúdo do comentário

        Returns:
            True se sucesso
        """
        await self.initialize()

        if not self._repo_obj:
            return False

        try:
            issue = self._repo_obj.get_issue(issue_number)
            issue.create_comment(body)

            logger.info(f"Comment posted to Issue #{issue_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to post issue comment: {e}")
            return False

    async def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
    ) -> Optional[Issue]:
        """
        Cria uma nova Issue.

        Args:
            title: Título
            body: Descrição
            labels: Labels a adicionar

        Returns:
            Issue criada
        """
        await self.initialize()

        if not self._repo_obj:
            return None

        try:
            issue = self._repo_obj.create_issue(
                title=title,
                body=body,
                labels=labels or [],
            )

            return Issue(
                number=issue.number,
                title=issue.title,
                body=issue.body or "",
                author=issue.user.login,
                labels=[l.name for l in issue.labels],
                status=issue.state,
                url=issue.html_url,
            )

        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return None

    async def close_issue(
        self,
        issue_number: int,
        comment: Optional[str] = None,
    ) -> bool:
        """
        Fecha uma Issue.

        Args:
            issue_number: Número da issue
            comment: Comentário de fechamento opcional

        Returns:
            True se sucesso
        """
        await self.initialize()

        if not self._repo_obj:
            return False

        try:
            issue = self._repo_obj.get_issue(issue_number)

            if comment:
                issue.create_comment(comment)

            issue.edit(state="closed")

            logger.info(f"Issue #{issue_number} closed")
            return True

        except Exception as e:
            logger.error(f"Failed to close issue: {e}")
            return False

    # ============================================================
    # REPOSITORY
    # ============================================================

    async def get_file_content(
        self,
        file_path: str,
        ref: str = "main",
    ) -> Optional[str]:
        """
        Obtém conteúdo de um arquivo do repositório.

        Args:
            file_path: Caminho do arquivo
            ref: Branch/commit/tag

        Returns:
            Conteúdo do arquivo
        """
        await self.initialize()

        if not self._repo_obj:
            return None

        try:
            content = self._repo_obj.get_contents(file_path, ref=ref)
            return content.decoded_content.decode("utf-8")

        except Exception as e:
            logger.error(f"Failed to get file content: {e}")
            return None

    async def get_repo_info(self) -> Dict[str, Any]:
        """
        Obtém informações do repositório.

        Returns:
            Dict com informações
        """
        await self.initialize()

        if not self._repo_obj:
            return {}

        return {
            "name": self._repo_obj.name,
            "full_name": self._repo_obj.full_name,
            "description": self._repo_obj.description,
            "default_branch": self._repo_obj.default_branch,
            "language": self._repo_obj.language,
            "stars": self._repo_obj.stargazers_count,
            "forks": self._repo_obj.forks_count,
            "open_issues": self._repo_obj.open_issues_count,
            "url": self._repo_obj.html_url,
        }

    # ============================================================
    # UTILITIES
    # ============================================================

    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do cliente"""
        await self.initialize()

        return {
            "status": "healthy" if self._initialized else "unhealthy",
            "repo": self.repo,
            "authenticated": self._github is not None,
            "repo_accessible": self._repo_obj is not None,
        }
