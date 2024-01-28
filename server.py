import asyncio
import logging
import os

from aiohttp import web
import aiofiles
from dotenv import load_dotenv


logger = logging.getLogger("asyncio_download_service")


async def archive(request):
    archive_name = request.match_info.get("archive_hash")
    photo_path = os.path.join(os.getenv("PHOTO_PATH", "photo"), archive_name)
    delay = os.getenv("DELAY", "0")

    if not os.path.exists(photo_path) or archive_name is None:
        print("not exist")
        async with aiofiles.open("html/error.html", mode="r") as error_file:
            error_contents = await error_file.read()
        return web.Response(text=error_contents, content_type="text/html")

    response = web.StreamResponse()
    response.headers["Content-Disposition"] = "attachment; filename=photos.zip"
    await response.prepare(request)

    zip_process = await asyncio.create_subprocess_exec(
        "zip",
        "-r",
        "-0",
        "-",
        "photos.zip",
        ".",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=photo_path,
    )

    try:
        download_step = 1
        while not zip_process.stdout.at_eof():
            archive_part = await zip_process.stdout.read(510200)
            await response.write(archive_part)
            await asyncio.sleep(int(delay))
            logger.info(f"Загружена {download_step} часть архива {archive_name}")
            download_step += 1
        return response

    except BaseException as error:
        logger.error(f"{error} - Скачивание прервано")
        await asyncio.sleep(1)

    finally:
        if zip_process.returncode == 0:
            logger.info(f"Архив {archive_name} успешно загружен")
        if zip_process.returncode is None:
            logger.info(f"Загрузка архива {archive_name} прервана")
            zip_process.terminate()
            await zip_process.communicate()


async def handle_index_page(request):
    async with aiofiles.open("html/index.html", mode="r") as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type="text/html")


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(
        format="%(levelname)-8s [%(asctime)s] %(message)s", level=logging.INFO
    )
    if os.getenv("LOGGING", "False").lower() in ("false", "0", "f"):
        logging.disable()

    app = web.Application()
    app.add_routes(
        [
            web.get("/", handle_index_page),
            web.get("/archive/{archive_hash}/", archive),
        ]
    )
    web.run_app(app)
