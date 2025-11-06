"""Google Drive toolkit for downloading documents to workspace.

Modified version that accepts OAuth credentials directly instead of file paths.
This allows per-user credential management in the Release Manager.
"""

import json
from pathlib import Path
from typing import Any

from agno.tools import Toolkit
from google.oauth2.credentials import Credentials
from loguru import logger

from .gdrive_utils import GoogleDriveExporter, GoogleDriveExporterConfig


class GoogleDriveTools(Toolkit):
    """Toolkit for downloading and managing Google Drive documents.

    This version accepts OAuth credentials directly, allowing per-user
    credential management without relying on file-based token storage.
    """

    def __init__(
        self,
        credentials: Credentials,
        workspace_dir: Path | None = None,
        **kwargs,
    ):
        """Initialize Google Drive toolkit with OAuth credentials.

        Args:
            credentials: Google OAuth2 credentials (from token exchange)
            workspace_dir: Directory to save downloaded files (defaults to ./workspace)
            **kwargs: Additional arguments passed to parent Toolkit
        """
        self.workspace_dir = workspace_dir or Path("./workspace")
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Set up Google Drive exporter configuration
        config = GoogleDriveExporterConfig(
            target_directory=self.workspace_dir,
            export_format="md",  # Default to markdown for Google Docs
        )

        # Create exporter with pre-authenticated credentials
        self.exporter = GoogleDriveExporter(config=config, credentials=credentials)

        tools: list[Any] = [
            self.download_document,
            self.download_multiple_documents,
            self.list_supported_formats,
            self.get_user_info,
            self.extract_document_id,
        ]

        super().__init__(name="gdrive_tools", tools=tools, **kwargs)

    def download_document(
        self, url_or_id: str, format: str = "md", output_name: str | None = None
    ) -> str:
        """Download a Google Drive document to the workspace directory.

        Args:
            url_or_id: Google Drive URL or document ID
            format: Export format (pdf, docx, html, md, txt, csv, xlsx, pptx, etc.)
                - defaults to 'md'
            output_name: Optional custom output name (without extension)

        Returns:
            Success message with file paths or error message
        """
        try:
            logger.info(f"Downloading Google Drive document: {url_or_id}")

            # Set the export format in the config
            original_format = self.exporter.config.export_format
            # Type ignore needed as format parameter is more flexible than the Literal type
            self.exporter.config.export_format = format  # type: ignore[assignment]

            try:
                # Download the document
                exported_files = self.exporter.export_document(url_or_id, output_name=output_name)

                if not exported_files:
                    return f"Failed to download document: {url_or_id}"

                # Format the response
                file_list = []
                for fmt, path in exported_files.items():
                    file_list.append(f"  {fmt}: {path}")

                result = "Successfully downloaded document to workspace:\n" + "\n".join(file_list)
                logger.info(result)
                return result

            finally:
                # Restore original format
                self.exporter.config.export_format = original_format

        except Exception as e:
            error_msg = f"Error downloading document {url_or_id}: {e}"
            logger.error(error_msg)
            return error_msg

    def download_multiple_documents(self, urls_or_ids: list[str], format: str = "md") -> str:
        """Download multiple Google Drive documents to the workspace directory.

        Args:
            urls_or_ids: List of Google Drive URLs or document IDs
            format: Export format for all documents - defaults to 'md' for Google Docs

        Returns:
            Summary of download results
        """
        try:
            logger.info(f"Downloading {len(urls_or_ids)} Google Drive documents")

            # Set the export format
            original_format = self.exporter.config.export_format
            # Type ignore needed as format parameter is more flexible than the Literal type
            self.exporter.config.export_format = format  # type: ignore[assignment]

            try:
                results = self.exporter.export_multiple(urls_or_ids)

                success_count = len(results)
                total_count = len(urls_or_ids)

                result_lines = [f"Download completed: {success_count}/{total_count} documents"]

                for doc_id, files in results.items():
                    result_lines.append(f"\nDocument {doc_id}:")
                    for fmt, path in files.items():
                        result_lines.append(f"  {fmt}: {path}")

                result = "\n".join(result_lines)
                logger.info(result)
                return result

            finally:
                # Restore original format
                self.exporter.config.export_format = original_format

        except Exception as e:
            error_msg = f"Error downloading multiple documents: {e}"
            logger.error(error_msg)
            return error_msg

    def list_supported_formats(self, document_type: str = "document") -> str:
        """List supported export formats for different document types.

        Args:
            document_type: Type of document (document, spreadsheet, presentation)

        Returns:
            JSON formatted list of supported formats
        """
        try:
            if document_type.lower() == "spreadsheet":
                formats = self.exporter.SPREADSHEET_EXPORT_FORMATS
            elif document_type.lower() == "presentation":
                formats = self.exporter.PRESENTATION_EXPORT_FORMATS
            else:
                formats = self.exporter.DOCUMENT_EXPORT_FORMATS

            format_info = {}
            for key, fmt in formats.items():
                format_info[key] = {
                    "extension": fmt.extension,
                    "mime_type": fmt.mime_type,
                    "description": fmt.description,
                }

            result = {
                "document_type": document_type,
                "supported_formats": format_info,
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            error_msg = f"Error listing formats for {document_type}: {e}"
            logger.error(error_msg)
            return error_msg

    def get_user_info(self) -> str:
        """Get information about the currently authenticated Google user.

        Returns:
            User information or error message
        """
        try:
            user_info = self.exporter.get_authenticated_user_info()

            if not user_info:
                return "No user information available. Authentication may be required."

            result = {
                "authenticated_user": {
                    "display_name": user_info.get("displayName", "Unknown"),
                    "email": user_info.get("emailAddress", "Unknown"),
                    "photo_link": user_info.get("photoLink", ""),
                }
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            error_msg = f"Error getting user info: {e}"
            logger.error(error_msg)
            return error_msg

    def extract_document_id(self, url: str) -> str:
        """Extract document ID from a Google Drive URL.

        Args:
            url: Google Drive URL

        Returns:
            Document ID or error message
        """
        try:
            doc_id = self.exporter.extract_document_id(url)
            return f"Document ID: {doc_id}"

        except Exception as e:
            error_msg = f"Error extracting document ID from {url}: {e}"
            logger.error(error_msg)
            return error_msg
