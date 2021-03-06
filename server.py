import asyncio
import io
import os
import pathlib
import shutil
import tarfile
import tempfile
from pprint import pformat

import aiohttp
from debian.deb822 import Deb822
from sanic import Sanic
from sanic.log import LOGGING_CONFIG_DEFAULTS, logger
from sanic.response import file, raw, redirect
from sanic_prometheus import monitor
from urlobject import URLObject

from config import Config, configure_logging
from cran.models import Package, Status
from cran.registry import Registry

log_config = LOGGING_CONFIG_DEFAULTS.copy()
configure_logging(log_config)

app = Sanic(log_config=log_config)
app.config.from_object(Config)
app.registry: Registry = None
app.semaphore = asyncio.Semaphore(1)
app.compile_queue: asyncio.Queue = None


async def pass_through(to):
    resp = await app.http.get(to)
    return raw(
        await resp.read(),
        status=resp.status,
        headers=resp.headers,
        content_type=resp.content_type,
    )


async def add_to_cache(url: URLObject):
    package = app.registry.get_or_create(url)
    if package.status == Status.UNSEEN:
        package_archive = await app.http.get(url)

        if not package_archive.status == 200:
            return

        fileobj = io.BytesIO(await package_archive.read())
        fileobj.seek(0)
        untarred = tarfile.open(fileobj=fileobj, mode="r:*")
        meta = {}

        try:
            for f in untarred.getmembers():
                if f.name.endswith("DESCRIPTION"):
                    logger.debug(f"add_to_cache:found {f.name}")
                    meta = Deb822(untarred.extractfile(f).read().decode("utf8"))

            logger.debug(meta)
            package.name = meta.get("Package")
            package.version = meta.get("Version")
            if meta.get("NeedsCompilation") == "yes":
                temp_dir = tempfile.mkdtemp()
                untarred.extractall(temp_dir)
                package.fs_path = pathlib.Path(temp_dir) / meta.get("Package")
                package.status = Status.TOBUILD
                await app.compile_queue.put(package)
            else:
                package.status = Status.NONBINARY
        finally:
            untarred.close()
            fileobj.close()


@app.route("/healthz")
def healthz(_):
    return raw(
        b"",
        headers={"Cache-Control": "no-cache, no-store, max-age=0"},
        content_type="text/plain",
    )


@app.route("/src/contrib/PACKAGES")
async def packages(request):
    cran = URLObject(app.config.UPSTREAM_CRAN_SERVER_URL)  # URLObject
    to = cran.add_path(f"/src/contrib/PACKAGES")
    return await pass_through(to)


@app.route("/src/contrib/<package>.tar.gz")
@app.route("/src/contrib/<path:path>/<package>.tar.gz")
async def serve_tarfile(request, package, path=None):

    cran = URLObject(app.config.UPSTREAM_CRAN_SERVER_URL)
    to = cran.add_path(request.path)

    if not app.config.PASSIVE:
        binary_path = (
            app.config.BINARY_OUTPUT_PATH / f"{package}_R_x86_64-pc-linux-gnu.tar.gz"
        )
        if os.path.isfile(binary_path):
            return await file(binary_path)
        asyncio.ensure_future(add_to_cache(to))

    logger.info(f"serve_tarfile: Redirecting [302] to {to}")
    return redirect(to)


@app.route("/")
@app.route("/<path:path>")
async def home(request, path="/"):
    cran = URLObject(app.config.UPSTREAM_CRAN_SERVER_URL)
    to = cran.add_path(path)
    logger.info(f"Proxying to {to}")
    return await pass_through(to)


# Lifecycle hooks


@app.listener("before_server_start")
async def setup(app, loop):
    # setup the queue
    app.compile_queue = asyncio.Queue(loop=loop)

    # fresh registry
    app.registry = Registry()

    # setup the session
    timeout = aiohttp.ClientTimeout(total=30)
    session = aiohttp.ClientSession(loop=loop, timeout=timeout)
    app.http = session


@app.listener("after_server_start")
async def compiler(app, loop):
    subprocess_extra_args = {}

    if not app.debug:
        # if not debug mode, don't put the output of the compile into the logs
        subprocess_extra_args = {
            k: asyncio.subprocess.DEVNULL for k in ["stdin", "stdout", "stderr"]
        }

    while True:
        # only check every few seconds
        logger.debug(f"Registry: {pformat(app.registry)}")
        await asyncio.sleep(3)
        async with app.semaphore:
            package: Package = await app.compile_queue.get()
            to_compile_path = package.fs_path
            try:
                proc = await asyncio.create_subprocess_shell(
                    f"""
                    BIN_DIR=$(/home/app/scripts/build.sh {to_compile_path} {app.config.BINARY_OUTPUT_PATH} | tail -1) &&
                    /home/app/scripts/fatten.sh $BIN_DIR
                    """,
                    limit=100,
                    **subprocess_extra_args,
                )
                package.status = Status.BUILDING
                await asyncio.sleep(5)
                proc_status = await proc.wait()
                if proc_status > 0:
                    package.status = Status.FAILED
                else:
                    package.status = Status.BUILT
            finally:
                # delete the tempdir, './package/' will already be deleted by the build process
                shutil.rmtree(package.fs_path.parent)


@app.listener("after_server_stop")
async def aiohttp_teardown(app, loop):
    await app.http.close()


# Serve


def serve():
    monitor(app, endpoint_type="url").expose_endpoint()
    app.run(host="0.0.0.0", port=app.config.PORT, debug=app.config.DEBUG)
    loop = asyncio.get_event_loop()
    if not loop.is_closed():
        pending = asyncio.Task.all_tasks()
        loop.run_until_complete(asyncio.gather(*pending))


def init():
    app.config.BINARY_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    init()
    serve()
