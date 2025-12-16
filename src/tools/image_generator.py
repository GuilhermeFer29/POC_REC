"""
Ferramenta customizada para geração de imagens com suporte a image-to-image.
Substitui o NanoBananaTools do Agno, com suporte a imagens de referência.
Funciona como um Toolkit do Agno para ser usado pelo agente Fotógrafo.
"""
import os
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, List, Any
from uuid import uuid4

from PIL import Image as PILImage
from google import genai
from google.genai import types

from agno.tools.toolkit import Toolkit
from agno.tools.function import ToolResult
from agno.media import Image

logger = logging.getLogger(__name__)

# Variável global para armazenar a imagem de referência atual
_current_reference_image: Optional[str] = None


def set_reference_image(image_path: Optional[str]):
    """Define a imagem de referência para as próximas gerações."""
    global _current_reference_image
    _current_reference_image = image_path


def get_reference_image() -> Optional[str]:
    """Obtém a imagem de referência atual."""
    return _current_reference_image


ALLOWED_RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]


class ImageGeneratorTools(Toolkit):
    """
    Toolkit para geração de imagens com suporte a image-to-image.
    Substitui o NanoBananaTools com suporte a imagens de referência.
    """
    
    def __init__(
        self,
        model: str = "gemini-2.5-flash-image",
        aspect_ratio: str = "4:3",
        api_key: Optional[str] = None,
        enable_create_image: bool = True,
        **kwargs,
    ):
        self.model = model
        self.aspect_ratio = aspect_ratio
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if self.aspect_ratio not in ALLOWED_RATIOS:
            raise ValueError(f"Invalid aspect_ratio '{self.aspect_ratio}'. Supported: {', '.join(ALLOWED_RATIOS)}")
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY ou GEMINI_API_KEY não configurado")
        
        tools: List[Any] = []
        if enable_create_image:
            tools.append(self.create_image)
        
        super().__init__(name="image_generator", tools=tools, **kwargs)
    
    def create_image(self, prompt: str) -> ToolResult:
        """
        Gera uma imagem a partir de um prompt de texto.
        Se uma imagem de referência estiver configurada, usa para manter consistência visual.
        
        Args:
            prompt: Descrição detalhada da imagem a ser gerada
            
        Returns:
            ToolResult com a imagem gerada
        """
        try:
            client = genai.Client(api_key=self.api_key)
            
            # Configuração de geração
            cfg = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio=self.aspect_ratio),
            )
            
            # Montar conteúdo: texto + imagem de referência (se houver)
            contents: List[Any] = [prompt]
            
            ref_image_path = get_reference_image()
            if ref_image_path and Path(ref_image_path).exists():
                try:
                    ref_image = PILImage.open(ref_image_path)
                    contents = [prompt, ref_image]
                    logger.info(f"[ImageGenerator] Usando imagem de referência: {ref_image_path}")
                except Exception as e:
                    logger.warning(f"[ImageGenerator] Não foi possível carregar imagem de referência: {e}")
            
            # Gerar imagem
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=cfg,
            )
            
            generated_images: List[Image] = []
            response_str = ""
            
            if not hasattr(response, "candidates") or not response.candidates:
                return ToolResult(content="Nenhuma imagem foi gerada na resposta")
            
            # Processar cada candidato
            for candidate in response.candidates:
                if not hasattr(candidate, "content") or not candidate.content or not candidate.content.parts:
                    continue
                
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_str += part.text + "\n"
                    
                    if hasattr(part, "inline_data") and part.inline_data:
                        try:
                            image_data = part.inline_data.data
                            mime_type = getattr(part.inline_data, "mime_type", "image/png")
                            
                            if image_data:
                                pil_img = PILImage.open(BytesIO(image_data))
                                
                                # Salvar em buffer com formato correto
                                buffer = BytesIO()
                                image_format = "PNG" if "png" in mime_type.lower() else "JPEG"
                                pil_img.save(buffer, format=image_format)
                                buffer.seek(0)
                                
                                agno_img = Image(
                                    id=str(uuid4()),
                                    content=buffer.getvalue(),
                                    original_prompt=prompt,
                                )
                                generated_images.append(agno_img)
                                response_str += f"Imagem gerada com sucesso (ID: {agno_img.id}).\n"
                        
                        except Exception as img_exc:
                            logger.error(f"Falha ao processar dados da imagem: {img_exc}")
                            response_str += f"Falha ao processar imagem: {img_exc}\n"
            
            if generated_images:
                return ToolResult(
                    content=response_str.strip() or "Imagem(ns) gerada(s) com sucesso",
                    images=generated_images,
                )
            else:
                return ToolResult(
                    content=response_str.strip() or "Nenhuma imagem foi gerada",
                    images=None,
                )
        
        except Exception as exc:
            logger.error(f"Falha na geração de imagem: {exc}")
            return ToolResult(content=f"Erro ao gerar imagem: {str(exc)}")
