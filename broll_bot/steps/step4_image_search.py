"""
Image Search -- Find and download still images for each entity.
"""
from dataclasses import dataclass
from utils.image_client import search_images, download_image, screenshot_article
from PIL import Image
import os


@dataclass
class ImageAsset:
    filename: str
    filepath: str
    source_url: str
    entity_name: str
    description: str
    width: int
    height: int
    type: str
    search_query: str
    match_reasoning: str = ""
    highlight_text: str = ""


async def search_and_download_images(
    entities: list,
    output_dir: str,
    start_index: int = 1
) -> list[ImageAsset]:
    """Search for and download images for all entities."""
    os.makedirs(output_dir, exist_ok=True)
    assets = []
    counter = start_index

    for entity in entities:
        for query in entity.image_queries:
            results = search_images(query, max_results=5)

            for result in results:
                image_url = result['url']
                temp_path = os.path.join(output_dir, f"temp_{counter}.png")
                success = download_image(image_url, temp_path)

                if not success:
                    continue

                try:
                    img = Image.open(temp_path)
                    w, h = img.size
                    if w < 1280 or h < 720:
                        os.remove(temp_path)
                        continue
                except Exception:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    continue

                final_name = f"{counter}.png"
                final_path = os.path.join(output_dir, final_name)
                os.rename(temp_path, final_path)

                img_type = "photo"
                url_lower = image_url.lower()
                if any(d in url_lower for d in ['wsj.com', 'nytimes.com', 'bloomberg.com', 'ft.com']):
                    img_type = "article_screenshot"
                elif 'chart' in query.lower() or 'graph' in query.lower():
                    img_type = "chart"

                reasoning = (
                    f"Found via query '{query}' for entity '{entity.name}' (era: {entity.era}). "
                    f"Source: {result.get('source', 'unknown')}. "
                    f"Image type: {img_type}. Resolution: {w}x{h}."
                )

                assets.append(ImageAsset(
                    filename=final_name,
                    filepath=final_path,
                    source_url=image_url,
                    entity_name=entity.name,
                    description=f"{entity.name} - {query}",
                    width=w,
                    height=h,
                    type=img_type,
                    search_query=query,
                    match_reasoning=reasoning
                ))

                counter += 1

        if entity.type == 'quote' and entity.notes:
            article_path = os.path.join(output_dir, f"{counter}.png")
            success = await screenshot_article(entity.notes, article_path)
            if success:
                try:
                    img = Image.open(article_path)
                    w, h = img.size
                    assets.append(ImageAsset(
                        filename=f"{counter}.png",
                        filepath=article_path,
                        source_url=entity.notes,
                        entity_name=entity.name,
                        description=f"Article screenshot: {entity.name}",
                        width=w, height=h,
                        type="article_screenshot",
                        search_query=f"article screenshot for {entity.name}",
                        match_reasoning=f"Direct article screenshot for quote entity '{entity.name}'. Source: {entity.notes}",
                        highlight_text=entity.name
                    ))
                    counter += 1
                except Exception:
                    pass

    return assets
