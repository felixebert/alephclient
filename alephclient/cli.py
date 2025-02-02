import json
import click
import logging

from alephclient import settings
from alephclient.api import AlephAPI
from alephclient.errors import AlephException
from alephclient.tasks.crawldir import crawl_dir
from alephclient.tasks.bulkload import bulk_load

log = logging.getLogger(__name__)


@click.group()
@click.option('--host', default=settings.HOST, metavar="HOST", help="Aleph API host URL")  # noqa
@click.option('--api-key', default=settings.API_KEY, metavar="KEY", help="Aleph API key for authentication")  # noqa
@click.option('-r', '--retries', type=int, default=settings.MAX_TRIES, help="retries upon server failure")  # noqa
@click.pass_context
def cli(ctx, host, api_key, retries):
    """API client for Aleph API"""
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpstream').setLevel(logging.WARNING)
    if not host:
        raise click.BadParameter('Missing Aleph host URL')
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj['api'] = AlephAPI(host, api_key, retries=retries)


@cli.command()
@click.option('--casefile', is_flag=True, default=False, help='handle as case file')  # noqa
@click.option('-l', '--language', multiple=True, help="language hint: 2-letter language code (ISO 639)")  # noqa
@click.option('-f', '--foreign-id', required=True, help="foreign_id of the collection")  # noqa
@click.argument('path', type=click.Path(exists=True))
@click.pass_context
def crawldir(ctx, path, foreign_id, language=None, casefile=False):
    """Crawl a directory recursively and upload the documents in it to a
    collection."""
    try:
        config = {
            'label': path,
            'languages': language,
            'casefile': casefile
        }
        api = ctx.obj["api"]
        crawl_dir(api, path, foreign_id, config)
    except AlephException as exc:
        raise click.ClickException(str(exc))


@cli.command()
@click.argument('mapping_file')
@click.pass_context
def bulkload(ctx, mapping_file):
    """Trigger a load of structured entity data using the submitted mapping."""
    # TODO: When can we remove this?
    try:
        bulk_load(ctx.obj["api"], mapping_file)
    except AlephException as exc:
        raise click.ClickException(str(exc))


@cli.command('write-entities')
@click.option('-i', '--infile', type=click.File('r'), default='-')  # noqa
@click.option('-f', '--foreign-id', required=True, help="foreign_id of the collection")  # noqa
@click.option('-m', '--merge', is_flag=True, default=False, help="update entities in place")  # noqa
@click.option('--force', is_flag=True, default=False, help="continue after server errors")  # noqa
@click.option('--unsafe', is_flag=True, default=False, help="disable server-side validation")  # noqa
@click.pass_context
def write_entities(ctx, infile, foreign_id, merge=False, force=False,
                   unsafe=False):
    """Read entities from standard input and index them."""
    api = ctx.obj["api"]
    try:
        collection = api.load_collection_by_foreign_id(foreign_id, {})
        collection_id = collection.get('id')

        def read_json_stream(stream):
            count = 0
            while True:
                line = stream.readline()
                if not line:
                    return
                count += 1
                if count % 1000 == 0:
                    log.info("[%s] Bulk load entities: %s...",
                             foreign_id, count)
                yield json.loads(line)

        api.write_entities(collection_id, read_json_stream(infile),
                           merge=merge, unsafe=unsafe, force=force)
    except AlephException as exc:
        raise click.ClickException(exc.message)
    except BrokenPipeError:
        raise click.Abort()


@cli.command('stream-entities')
@click.option('-o', '--outfile', type=click.File('w'), default='-')  # noqa
@click.option('-f', '--foreign-id', help="foreign_id of the collection")
@click.pass_context
def stream_entities(ctx, outfile, foreign_id):
    """Load entities from the server and print them to stdout."""
    api = ctx.obj["api"]
    try:
        include = ['id', 'schema', 'properties']
        collection = api.get_collection_by_foreign_id(foreign_id)
        if collection is None:
            raise click.BadParameter("Collection %r not found!" % foreign_id)
        for entity in api.stream_entities(collection_id=collection.get('id'),
                                          include=include,
                                          decode_json=False):
            outfile.write(json.dumps(entity))
            outfile.write('\n')
    except AlephException as exc:
        raise click.ClickException(exc.message)
    except BrokenPipeError:
        raise click.Abort()


if __name__ == "__main__":
    cli()
