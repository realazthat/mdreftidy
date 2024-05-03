"""
Reorder refence links in markdown files.
"""
import argparse
import sys
import textwrap
import warnings
from pathlib import Path
from shutil import get_terminal_size
from typing import Optional

import colorama
import mistletoe
from mistletoe.markdown_renderer import MarkdownRenderer
from rich.console import Console
from rich_argparse import RichHelpFormatter

from . import _build_version
from .mdreftidy import (BlockSorter, ErrorChecker, MoveToBottom,
                        RemoveEmptyRefBlocks, RemoveUnused, Renumberer)


def _GetProgramName() -> str:
  if __package__:
    # Use __package__ to get the base package name
    base_module_path = __package__
    # Infer the module name from the file path, with assumptions about the structure
    module_name = Path(__file__).stem
    # Construct what might be the intended full module path
    full_module_path = f'{base_module_path}.{module_name}' if base_module_path else module_name
    return f'python -m {full_module_path}'
  else:
    return sys.argv[0]


class _CustomRichHelpFormatter(RichHelpFormatter):

  def __init__(self, *args, **kwargs):
    if kwargs.get('width') is None:
      width, _ = get_terminal_size()
      if width == 0:
        warnings.warn('Terminal width was set to 0, using default width of 80.',
                      RuntimeWarning,
                      stacklevel=0)
        # This is the default in get_terminal_size().
        width = 80
      # This is what HelpFormatter does to the width returned by
      # `get_terminal_size()`.
      width -= 2
      kwargs['width'] = width
    super().__init__(*args, **kwargs)


def _GetInput(args: argparse.Namespace) -> str:
  path_str = args.input
  if path_str == '-':
    return sys.stdin.read()

  path = Path(path_str)
  if not path.exists():
    raise FileNotFoundError(f'File not found: {path_str}')

  with path.open() as fin:
    return fin.read()


def _DumpOutput(args: argparse.Namespace, output: str):
  path_str = args.output
  if args.inplace:
    path_str = args.input

  if path_str == '-':
    sys.stdout.write(output)
    return

  path = Path(path_str)
  with path.open('w') as fout:
    fout.write(output)


def main():
  console = Console(file=sys.stderr)
  args: Optional[argparse.Namespace] = None
  try:
    # Windows<10 requires this.
    colorama.init()
    p = argparse.ArgumentParser(prog=_GetProgramName(),
                                description=__doc__,
                                formatter_class=_CustomRichHelpFormatter)

    p.add_argument('input',
                   type=str,
                   help='Input markdown file, use "-" for stdin.')
    p.add_argument('-i',
                   '--inplace',
                   action='store_true',
                   help='Update the file in place. Default: False.')
    p.add_argument(
        '-o',
        '--output',
        dest='output',
        type=str,
        default='-',
        help='Output markdown file, use "-" for stdout. Default: stdout.')
    p.add_argument('--renumber',
                   action='store_true',
                   help='Renumber reference definitions.')
    p.add_argument('--remove-unused',
                   action='store_true',
                   help='Remove unused reference definitions.')
    p.add_argument('--move-to-bottom',
                   action='store_true',
                   help='Move reference definitions to the bottom of the file.')
    p.add_argument('--sort-ref-blocks',
                   action='store_true',
                   help='Sort all blocks of references.')
    p.add_argument(
        '-c',
        '--check',
        action='store_true',
        help='Return non-zero if there are any changes. Nothing is output.')
    p.add_argument('--version',
                   action='version',
                   version=_build_version,
                   help='Show the version and exit.')

    args = p.parse_args()
    check: bool = args.check
    renumber: bool = args.renumber
    remove_unused: bool = args.remove_unused
    remove_unused_ref_blocks: bool = remove_unused
    move_to_bottom: bool = args.move_to_bottom
    sort_ref_blocks: bool = args.sort_ref_blocks

    with MarkdownRenderer() as renderer:
      doc = mistletoe.Document(_GetInput(args))

      try:
        is_changed = set()
        ErrorChecker(console=console).Check(doc)

        if remove_unused:
          remover = RemoveUnused(console=console)
          remover.RemoveUnused(doc)
          if remover.IsChanged():
            is_changed.add('RemoveUnused')

          ErrorChecker(console=console).Check(doc)

        if remove_unused_ref_blocks:
          empty_blocks_remover = RemoveEmptyRefBlocks(console=console)
          empty_blocks_remover.RemoveEmptyRefBlocks(doc)
          if empty_blocks_remover.IsChanged():
            is_changed.add('RemoveEmptyRefBlocks')

          ErrorChecker(console=console).Check(doc)

        if renumber:
          renumberer = Renumberer(console=console)
          renumberer.Renumber(doc)
          if renumberer.IsChanged():
            is_changed.add('Renumberer')

          ErrorChecker(console=console).Check(doc)

        if move_to_bottom:
          mover = MoveToBottom(console=console)
          mover.MoveToBottom(doc)
          if mover.IsChanged():
            is_changed.add('MoveToBottom')

          ErrorChecker(console=console).Check(doc)

        if sort_ref_blocks:
          sorter = BlockSorter(console=console)
          sorter.SortBlocks(doc)
          if sorter.IsChanged():
            is_changed.add('BlockSorter')

          ErrorChecker(console=console).Check(doc)

        if check:
          if is_changed:
            console.print('Changes detected.', style='bold red')
            console.print('Changed passes:', is_changed, style='bold red')
            sys.exit(1)
          else:
            console.print('No changes detected.', style='bold green')
            sys.exit(0)
          return
        _DumpOutput(args, renderer.render(doc))
      except Exception:
        console.print_exception()
        print('current doc:', file=sys.stderr)
        print(textwrap.indent(renderer.render(doc), "  |", lambda line: True),
              file=sys.stderr)
        raise

  except Exception:
    console.print_exception()
    if args:
      console.print('args:', args._get_kwargs(), style='bold red')

    sys.exit(1)
    return


if __name__ == '__main__':
  main()
