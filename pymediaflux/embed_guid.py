import os
import click
import exiftool

# Metadata fields for Identifier 1 (Mediaflux GUID)
IDENTIFIER_1_FIELDS = [
    "XMP-dc:Identifier",  # Dublin Core in XMP
    "IPTC:OriginalTransmissionReference",  # IPTC field 2:103 (legacy field)
    "XMP-Iptc4xmpCore:OriginalTransmissionReference",  # IPTC Core schema in XMP
    "XMP-xmpMM:DocumentID",  # XMP Metadata Management schema
]

# Metadata fields for Identifier 2 (Mediaflux Export GUID)
IDENTIFIER_2_FIELDS = [
    "XMP:MediafluxExportGUID",  # Custom XMP field
    "IPTC:SpecialInstructions",  # IPTC field 2:40 (legacy field)
    "XMP-Iptc4xmpCore:Instructions",  # IPTC Core schema in XMP
]


def embed_metadata(
    input_file, output_file, mediaflux_guid=None, mediaflux_export_guid=None
):
    """Embed metadata into a single file."""
    with exiftool.ExifTool() as et:
        # Prepare commands
        commands = []
        if mediaflux_guid:
            for field in IDENTIFIER_1_FIELDS:
                commands.append(f"-{field}={mediaflux_guid}")
        if mediaflux_export_guid:
            for field in IDENTIFIER_2_FIELDS:
                commands.append(f"-{field}={mediaflux_export_guid}")

        # Add output file command
        if input_file != output_file:
            commands.append("-o")
            commands.append(output_file)

        # Execute commands
        print(commands)
        et.execute(*[cmd.encode() for cmd in commands], input_file.encode())


@click.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True, readable=True))
@click.option(
    "-g", "--guid", "mediaflux_guid", help="Mediaflux GUID to embed (Identifier 1)."
)
@click.option(
    "-e",
    "--export-guid",
    "mediaflux_export_guid",
    help="Mediaflux Export GUID to embed (Identifier 2).",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    type=click.Path(file_okay=False, writable=True),
    help="Directory to write modified files.",
)
def main(files, mediaflux_guid, mediaflux_export_guid, output_dir):
    """
    Embed metadata into image files.

    FILES: List of image files to process.

    At least one of --guid or --export-guid must be provided.
    If --output is specified, modified files are written to the output directory.
    """
    if not mediaflux_guid and not mediaflux_export_guid:
        click.echo(
            "Error: At least one of --guid or --export-guid must be provided.", err=True
        )
        return

    if not files:
        click.echo(
            "Error: No files provided. Please specify at least one file.", err=True
        )
        return

    # Process each file
    for input_file in files:
        output_file = input_file
        if output_dir:
            # Create output file path in the specified output directory
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, os.path.basename(input_file))

        click.echo(f"Processing file: {input_file}")
        try:
            embed_metadata(
                input_file, output_file, mediaflux_guid, mediaflux_export_guid
            )
            click.echo(f"Successfully wrote metadata to: {output_file}")
        except Exception as e:
            click.echo(f"Error processing {input_file}: {e}", err=True)


if __name__ == "__main__":
    main()
