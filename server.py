import asyncio
import logging
import os

from aiohttp import web
import aiofiles


logger = logging.getLogger("asyncio_download_service")


async def archive(request):
    archive_name = request.match_info.get("archive_hash", "archive")

    if not os.path.exists(f"photos/{archive_name}"):
        async with aiofiles.open("error.html", mode="r") as error_file:
            error_contents = await error_file.read()
        return web.Response(text=error_contents, content_type="text/html")

    response = web.StreamResponse()
    response.headers["Content-Disposition"] = "attachment; filename=photos.zip"
    await response.prepare(request)

    process = await asyncio.create_subprocess_exec(
        "zip",
        "-r",
        "-0",
        "-",
        "photos.zip",
        ".",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=f"photos/{archive_name}",
    )

    step = 1
    while True:
        try:
            archive_part = await process.stdout.read(510200)
            await response.write(archive_part)
            logger.info(f"Загружена {step} часть архива {archive_name}")
            step += 1
            if process.stdout.at_eof():
                return response
        except ConnectionResetError as error:
            logger.error(
                f"Ошибка сетевого соединения - {error}. Скачивание остановлено"
            )
            break


async def handle_index_page(request):
    async with aiofiles.open("index.html", mode="r") as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type="text/html")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)-8s [%(asctime)s] %(message)s", level=logging.INFO
    )
    logger.setLevel(logging.INFO)
    app = web.Application()
    app.add_routes(
        [
            web.get("/", handle_index_page),
            web.get("/archive/{archive_hash}/", archive),
        ]
    )
    web.run_app(app)
