/**
 * The class merger, re-exported rather than re-implemented.
 *
 * `cn` is four lines of `clsx` and `tailwind-merge`, which is exactly why it gets written
 * again in every repository that installs shadcn — and two `cn`s built against two
 * `tailwind-merge` versions resolve conflicting utilities differently, so the same
 * className produces a different result in two apps that believe they share a design
 * system. This file is the sanctioned shim: `components.json` points shadcn's generator
 * at `@/lib/utils`, the generator keeps working, and the implementation stays the
 * package's.
 */
export { cn, truncateMiddle } from '@viglet/viglet-design-system'
