"""
Serviço para download e persistência de imagens.
Salva imagens localmente em media/ que é montado como volume Docker.
"""

import httpx
import hashlib
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


class ImageDownloader:
    def __init__(self, base_path: str = "media"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_extension(self, url: str, content_type: str | None = None) -> str:
        """Determina a extensão do arquivo baseado na URL ou content-type."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if path.endswith('.png'):
            return '.png'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            return '.jpg'
        elif path.endswith('.gif'):
            return '.gif'
        elif path.endswith('.webp'):
            return '.webp'
        
        if content_type:
            if 'png' in content_type:
                return '.png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                return '.jpg'
            elif 'gif' in content_type:
                return '.gif'
            elif 'webp' in content_type:
                return '.webp'
        
        return '.jpg'

    def _generate_filename(self, url: str, prefix: str = "") -> str:
        """Gera um nome de arquivo único baseado na URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        return f"{prefix}_{url_hash}" if prefix else url_hash

    async def download_image(
        self,
        url: str,
        subdir: str,
        filename: str | None = None,
        prefix: str = "",
    ) -> Optional[str]:
        """
        Baixa uma imagem e salva localmente.
        
        Args:
            url: URL da imagem
            subdir: Subdiretório dentro de media/ (ex: 'ingredientes', 'receitas')
            filename: Nome do arquivo (opcional, gera automaticamente se não fornecido)
            prefix: Prefixo para o nome do arquivo
            
        Returns:
            Caminho relativo da imagem salva ou None se falhar
        """
        if not url:
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return None
                
                content_type = response.headers.get('content-type', '')
                extension = self._get_extension(url, content_type)
                
                if not filename:
                    filename = self._generate_filename(url, prefix)
                
                if not filename.endswith(extension):
                    filename = f"{filename}{extension}"
                
                save_dir = self.base_path / subdir
                save_dir.mkdir(parents=True, exist_ok=True)
                
                file_path = save_dir / filename
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                return f"media/{subdir}/{filename}"
                
        except Exception as e:
            print(f"Erro ao baixar imagem {url}: {e}")
            return None

    async def download_ingrediente_image(
        self,
        url: str,
        ingrediente_id: int,
        nome: str,
    ) -> Optional[str]:
        """Baixa imagem de um ingrediente."""
        safe_nome = "".join(c if c.isalnum() else "_" for c in nome.lower())[:30]
        filename = f"ing_{ingrediente_id}_{safe_nome}"
        return await self.download_image(url, "ingredientes", filename=filename)

    async def download_receita_image(
        self,
        url: str,
        receita_id: int,
        nome: str,
    ) -> Optional[str]:
        """Baixa imagem de uma receita."""
        safe_nome = "".join(c if c.isalnum() else "_" for c in nome.lower())[:30]
        filename = f"rec_{receita_id}_{safe_nome}"
        return await self.download_image(url, "receitas", filename=filename)

    async def download_produto_image(
        self,
        url: str,
        produto_id: int,
    ) -> Optional[str]:
        """Baixa imagem de um produto."""
        filename = f"produto_{produto_id}"
        return await self.download_image(url, "produtos", filename=filename)

    def get_local_url(self, relative_path: str) -> str:
        """Converte caminho relativo para URL servida pelo FastAPI."""
        return f"/{relative_path}"

    def image_exists(self, relative_path: str) -> bool:
        """Verifica se uma imagem já existe localmente."""
        if not relative_path:
            return False
        full_path = self.base_path.parent / relative_path
        return full_path.exists()
