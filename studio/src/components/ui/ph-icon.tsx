'use client';

import {
  MagnifyingGlass,
  TreeStructure,
  ClipboardText,
  Link,
  Lightning,
  PaintBrush,
  RocketLaunch,
  PuzzlePiece,
  Warning,
  Plus,
  CaretLeft,
  CaretRight,
  SquaresFour,
  Sparkle,
  Heart,
  CheckCircle,
  type IconProps,
} from '@phosphor-icons/react';

const ICON_MAP = {
  'magnifying-glass': MagnifyingGlass,
  'tree-structure': TreeStructure,
  'clipboard-text': ClipboardText,
  'link': Link,
  'lightning': Lightning,
  'paint-brush': PaintBrush,
  'rocket-launch': RocketLaunch,
  'puzzle-piece': PuzzlePiece,
  'warning': Warning,
  'plus': Plus,
  'caret-left': CaretLeft,
  'caret-right': CaretRight,
  'squares-four': SquaresFour,
  'sparkle': Sparkle,
  'heart': Heart,
  'check-circle': CheckCircle,
} as const;

export type PhIconName = keyof typeof ICON_MAP;

interface PhIconProps extends Omit<IconProps, 'name'> {
  name: PhIconName;
}

export function PhIcon({ name, ...props }: PhIconProps) {
  const IconComponent = ICON_MAP[name];
  if (!IconComponent) return null;
  return <IconComponent {...props} />;
}
