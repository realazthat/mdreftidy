import textwrap
from collections import defaultdict
from functools import partial
from typing import Dict, List, Optional

import yaml
from mistletoe.block_token import Document
from mistletoe.markdown_renderer import (LinkReferenceDefinition,
                                         LinkReferenceDefinitionBlock)
from mistletoe.span_token import Image, Link
from mistletoe.token import Token
from rich.console import Console
from typing_extensions import Any, Literal, Protocol


class _Visitor(Protocol):

  def __call__(self, *, ancestors: List[Token], token: Token,
               children: Optional[List[Token]], order: Literal['pre',
                                                               'post']) -> bool:
    """
    When order=='pre', returning True means should descend into children, False means to skip children.

    When order=='post', return value is ignored.
    """
    ...


def _GetLineNumber(token: Token,
                   ancestors: Optional[List[Token]]) -> Optional[int]:
  if hasattr(token, "line_number"):
    line_number = getattr(token, "line_number")
    if line_number is not None:
      if not isinstance(line_number, int):
        raise AssertionError(
            f'Expected line_number to be an int, but got {type(line_number)}')
      return line_number

  if ancestors is not None:
    for ancestor in ancestors:
      ancestor_line_number: Optional[int] = _GetLineNumber(ancestor,
                                                           ancestors=None)
      if ancestor_line_number is not None:
        return ancestor_line_number
  return None


def _DumpTokenInfo(token: Token, ancestors: Optional[List[Token]]) -> str:
  return yaml.dump({
      'type': type(token).__name__,
      'token': token,
      'line_number': _GetLineNumber(token, ancestors=ancestors)
  })


def _GetChildren(token: Token) -> Optional[List[Token]]:
  if not hasattr(token, 'children'):
    return None
  children_any: Any = token.children  # type: ignore
  if not isinstance(children_any, list):
    raise ValueError(
        f'Expected children to be a list, but got {type(children_any)}'
        f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=None), "  ")}'
    )
  for child in children_any:
    if not isinstance(child, Token):
      raise ValueError(
          f'Expected child to be a Token, but got {type(child)}'
          f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=None), "  ")}'
      )

  children: List[Token] = children_any
  return children


def _Traverse(*, token: Token, ancestors: List[Token], visitor: _Visitor):
  """Update the text contents of paragraphs and headings within this block,
    and recursively within its children."""
  children: Optional[List[Token]] = _GetChildren(token)

  should_descend: bool = visitor(ancestors=ancestors,
                                 token=token,
                                 children=children,
                                 order='pre')

  if children is not None and should_descend:
    for child in children:
      _Traverse(token=child, ancestors=ancestors + [token], visitor=visitor)
  visitor(ancestors=ancestors, token=token, children=children, order='post')


def _RemoveToken(parent: Optional[Token], token: Token):
  if parent is None:
    raise ValueError(
        f'Expected parent to be a Token, but got None'
        f'\n parent: None'
        f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=None), "  ")}'
    )
  children: Optional[List[Token]] = _GetChildren(parent)
  if children is None:
    raise ValueError(
        f'Expected parent to have children, but got no children'
        f'\n parent:\n{textwrap.indent(_DumpTokenInfo(parent, ancestors=None), "  ")}'
        f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=None), "  ")}'
    )
  children.remove(token)


def _GetOrCreateFootRefBlock(
    document: Document) -> LinkReferenceDefinitionBlock:
  last_token: Optional[
      Token] = document.children[-1] if document.children else None
  if isinstance(last_token, LinkReferenceDefinitionBlock):
    return last_token
  ref_block = LinkReferenceDefinitionBlock(matches=[])
  document.children.append(ref_block)
  return ref_block


def _GetRefBlockName(token: LinkReferenceDefinitionBlock) -> str:
  if not isinstance(token, LinkReferenceDefinitionBlock):
    raise ValueError(
        f'Expected token to be a LinkReferenceDefinitionBlock, but got {type(token)}'
        f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=None), "  ")}'
    )
  for child in token.children:
    if not isinstance(child, LinkReferenceDefinition):
      raise ValueError(
          f'Expected children to be a list of LinkReferenceDefinition, but got {type(child)}'
          f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=None), "  ")}'
      )
    return child.label
  return 'N/A'


class ErrorChecker:

  def __init__(self, console: Console) -> None:
    self._next_relabel: int = 1
    self._console = console

    self._label2relabel: Dict[str, int] = {}
    self._label2reftoken: Dict[str, Token] = {}
    self._label2links: Dict[str, List[Token]] = defaultdict(list)

  def IsChanged(self) -> bool:
    return False

  def _ScanVisitor(self, *, ancestors: List[Token], token: Token,
                   children: Optional[List[Token]],
                   order: Literal['pre', 'post']) -> bool:
    if order == 'pre':
      return True

    label: str
    if isinstance(token, Image):
      if token.label is not None:
        label = token.label
        self._label2links[label].append(token)
        if label in self._label2relabel:
          return True
        self._label2relabel[token.label] = self._next_relabel
        self._next_relabel += 1
    elif isinstance(token, Link):
      if token.label is not None:
        label = token.label
        self._label2links[label].append(token)
        if label in self._label2relabel:
          return True
        self._label2relabel[token.label] = self._next_relabel
        self._next_relabel += 1
    if isinstance(token, (LinkReferenceDefinition)):
      if not isinstance(token.label, str):
        raise ValueError(
            f'Expected label of reference to be a string, but got {type(token.label)}'
        )
      label = token.label
      if label in self._label2reftoken:
        prev_token = self._label2reftoken[label]
        raise ValueError(
            f'Duplicate reference label: {label}'
            f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=ancestors), "  ")}'
            f'\n prev_token:\n{textwrap.indent(_DumpTokenInfo(prev_token, ancestors=None), "  ")}'
        )
      self._label2reftoken[label] = token
    else:
      pass
    return True

  def Check(self, document: Document):
    _Traverse(token=document, ancestors=[], visitor=self._ScanVisitor)


class Renumberer:

  def __init__(self, console: Console) -> None:
    self._next_relabel: int = 1
    self._console = console

    self._label2relabel: Dict[str, int] = {}
    self._label2reftoken: Dict[str, Token] = {}
    self._label2links: Dict[str, List[Token]] = defaultdict(list)
    self._is_changed = False

  def IsChanged(self) -> bool:
    return self._is_changed

  def _ScanVisitor(self, *, ancestors: List[Token], token: Token,
                   children: Optional[List[Token]],
                   order: Literal['pre', 'post']) -> bool:
    if order == 'pre':
      return True

    label: str
    if isinstance(token, Image):
      if token.label is not None:
        label = token.label
        self._label2links[label].append(token)
        if label in self._label2relabel:
          return True
        self._label2relabel[token.label] = self._next_relabel
        self._next_relabel += 1
    elif isinstance(token, Link):
      if token.label is not None:
        label = token.label
        self._label2links[label].append(token)
        if label in self._label2relabel:
          return True
        self._label2relabel[token.label] = self._next_relabel
        self._next_relabel += 1
    if isinstance(token, (LinkReferenceDefinition)):
      if not isinstance(token.label, str):
        raise ValueError(
            f'Expected label of reference to be a string, but got {type(token.label)}'
        )
      label = token.label
      if label in self._label2reftoken:
        prev_token = self._label2reftoken[label]
        raise ValueError(
            f'Duplicate reference label: {label}'
            f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=ancestors), "  ")}'
            f'\n prev_token:\n{textwrap.indent(_DumpTokenInfo(prev_token, ancestors=None), "  ")}'
        )
      self._label2reftoken[label] = token
    else:
      pass
    return True

  def _UpdateVisitor(self, *, ancestors: List[Token], token: Token,
                     children: Optional[List[Token]],
                     order: Literal['pre', 'post']) -> bool:
    if order == 'pre':
      return True

    if isinstance(token, (LinkReferenceDefinition)):
      if not isinstance(token.label, str):
        raise ValueError(
            f'Expected label of reference to be a string, but got {type(token.label)}'
        )

      label = token.label
      if label in self._label2relabel:
        # Fix the reference.
        new_label = str(self._label2relabel[token.label])
        if token.label == new_label:
          return True
        token.label = new_label
        self._is_changed = True
        self._console.print(f'Reference relabeled: {label} -> {new_label}',
                            style='blue')

        # Fix the links.
        for link_tokens in self._label2links[label]:
          if isinstance(link_tokens, Image):
            link_tokens.label = str(self._label2relabel[label])
          elif isinstance(link_tokens, Link):
            link_tokens.label = str(self._label2relabel[label])
          else:
            raise AssertionError(
                f'Expected link_tokens to be an Image or Link, but got {type(link_tokens)}'
            )
    return True

  def Renumber(self, document: Document):
    _Traverse(token=document, ancestors=[], visitor=self._ScanVisitor)

    # Unreferenced labels must be relabeled.
    for old_label in self._label2reftoken.keys():
      # If the label is already relabeled, skip it.
      if old_label in self._label2relabel:
        continue
      self._label2relabel[old_label] = self._next_relabel
      self._next_relabel += 1

    _Traverse(token=document, ancestors=[], visitor=self._UpdateVisitor)


class RemoveUnused:

  def __init__(self, console: Console) -> None:
    self._console = console
    self._is_changed = False
    self._label2link: Dict[str, List[Token]] = defaultdict(list)

  def IsChanged(self) -> bool:
    return self._is_changed

  def _ScanVisitor(self, *, ancestors: List[Token], token: Token,
                   children: Optional[List[Token]],
                   order: Literal['pre', 'post']) -> bool:
    if order == 'pre':
      return True

    if isinstance(token, (Image, Link)):
      if token.label is not None:
        label = token.label
        self._label2link[label].append(token)
    return True

  def _IsUnused(self, *, token: LinkReferenceDefinition) -> bool:
    if not isinstance(token.label, str):
      raise ValueError(
          f'Expected label of reference to be a string, but got {type(token.label)}'
      )
    label: str = token.label
    if label not in self._label2link:
      return True
    return len(self._label2link[label]) == 0

  def _RemoveUnusedVisitor(self, *, ancestors: List[Token], token: Token,
                           children: Optional[List[Token]],
                           order: Literal['pre', 'post']) -> bool:
    if order == 'pre':
      return True

    if not isinstance(token, LinkReferenceDefinition):
      return True
    if len(ancestors) == 0:
      raise ValueError(
          f'Expected ancestors of a LinkReferenceDefinition to be a LinkReferenceDefinitionBlock, but got empty'
          f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=None), "  ")}'
      )
    parent: Token = ancestors[-1]
    if not isinstance(parent, LinkReferenceDefinitionBlock):
      raise ValueError(
          f'Expected parent of a LinkReferenceDefinition to be a LinkReferenceDefinitionBlock, but got {type(parent)}'
          f'\n parent:\n{textwrap.indent(_DumpTokenInfo(parent, ancestors=ancestors[:-1]), "  ")}'
          f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=ancestors), "  ")}'
      )
    if not self._IsUnused(token=token):
      return True
    _RemoveToken(parent=parent, token=token)
    self._is_changed = True
    self._console.print(
        f'Unused reference removed: {token.label}',
        style='blue',
    )

    return True

  def RemoveUnused(self, document: Document):
    _Traverse(token=document, ancestors=[], visitor=self._ScanVisitor)
    _Traverse(token=document, ancestors=[], visitor=self._RemoveUnusedVisitor)


class RemoveEmptyRefBlocks:

  def __init__(self, console: Console) -> None:
    self._console = console
    self._is_changed = False
    self._label2link: Dict[str, List[Token]] = defaultdict(list)

  def IsChanged(self) -> bool:
    return self._is_changed

  def _RemoveEmptyRefBlocksVisitor(self, *, ancestors: List[Token],
                                   token: Token,
                                   children: Optional[List[Token]],
                                   order: Literal['pre', 'post']) -> bool:
    if order == 'pre':
      return True

    if not isinstance(token, LinkReferenceDefinitionBlock):
      return True
    if children is not None and len(children) > 0:
      return True

    _RemoveToken(parent=ancestors[-1], token=token)
    self._is_changed = True
    self._console.print(
        f'Empty reference block removed',
        style='blue',
    )
    return True

  def RemoveEmptyRefBlocks(self, document: Document):
    _Traverse(token=document,
              ancestors=[],
              visitor=self._RemoveEmptyRefBlocksVisitor)


class MoveToBottom:

  def __init__(self, console: Console) -> None:
    self._console = console
    self._is_changed = False

  def IsChanged(self) -> bool:
    return self._is_changed

  def _MoveToBottomVisitor(self, *, ref_block: LinkReferenceDefinitionBlock,
                           ancestors: List[Token], token: Token,
                           children: Optional[List[Token]],
                           order: Literal['pre', 'post']) -> bool:
    if order == 'pre':
      return True

    if not isinstance(token, LinkReferenceDefinitionBlock):
      return True

    if not ancestors:
      raise ValueError(
          f'Expected ancestors to be non-empty, but got empty'
          f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=None), "  ")}'
      )
    parent: Token = ancestors[-1]

    if token is ref_block:
      return True

    if not children or len(children) == 0:
      _RemoveToken(parent=parent, token=token)
      self._is_changed = True
      self._console.print(
          f'Empty reference block moved to the bottom (in other words, deleted)',
          style='blue')
      return True

    ref_children: List[LinkReferenceDefinition] = []
    first_label = _GetRefBlockName(token)
    for child in children:
      if not isinstance(child, LinkReferenceDefinition):
        raise ValueError(
            f'Expected children to be a list of LinkReferenceDefinition, but got {type(child)}'
            f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=ancestors), "  ")}'
        )
      ref_children.append(child)
      if first_label == 'N/A':
        first_label = child.label

    ref_block.children.extend(ref_children)
    _RemoveToken(parent=parent, token=token)
    self._is_changed = True
    self._console.print(
        f'Reference block starting with [{first_label}] moved to the bottom',
        style='blue',
    )

    return True

  def MoveToBottom(self, document: Document):
    ref_block = _GetOrCreateFootRefBlock(document)
    _Traverse(token=document,
              ancestors=[],
              visitor=partial(self._MoveToBottomVisitor, ref_block=ref_block))


class BlockSorter:

  def __init__(self, console: Console) -> None:
    self._console = console
    self._is_changed = False

  def IsChanged(self) -> bool:
    return self._is_changed

  def _GetRefLabel(self, token: Token, ancestors: List[Token]) -> str:
    if not isinstance(token, LinkReferenceDefinition):
      raise ValueError(
          f'Expected token to be a LinkReferenceDefinition (since it is a child of a LinkReferenceDefinitionBlock), but got {type(token)}'
          f'\n token:\n{textwrap.indent(_DumpTokenInfo(token, ancestors=None), "  ")}'
      )
    if not isinstance(token.label, str):
      raise ValueError(
          f'Expected label of reference to be a string, but got {type(token.label)}'
      )
    return token.label

  def _SortBlockVisitor(self, *, ancestors: List[Token], token: Token,
                        children: Optional[List[Token]],
                        order: Literal['pre', 'post']) -> bool:
    if order == 'pre':
      return True

    if not isinstance(token, LinkReferenceDefinitionBlock):
      return True

    if not children:
      return True

    old_children = list(children)
    children.sort(key=lambda child: self._GetRefLabel(
        child, ancestors=ancestors + [token]))
    if old_children == children:
      return True

    ref_block_name = _GetRefBlockName(token)
    self._is_changed = True
    self._console.print(
        f'Reference block starting with [{ref_block_name}] sorted',
        style='blue',
    )

    return False

  def SortBlocks(self, document: Document):
    _Traverse(token=document, ancestors=[], visitor=self._SortBlockVisitor)
