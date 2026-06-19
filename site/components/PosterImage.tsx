import type { ImgHTMLAttributes } from "react";

type PosterImageProps = ImgHTMLAttributes<HTMLImageElement> & {
  avifSrcSet?: string;
  webpSrcSet?: string;
  sizes?: string;
};

export function PosterImage({
  avifSrcSet,
  webpSrcSet,
  sizes = "(max-width: 640px) 342px, 500px",
  ...imgProps
}: PosterImageProps) {
  // avif variants are pruned from deploy to stay under CF Pages' 20k-file ceiling; webp
  // (~96% support) is the modern path, jpg the universal fallback. avifSrcSet is accepted
  // for API compatibility but intentionally not emitted as a <source> (its files are gone).
  if (!webpSrcSet) {
    return <img {...imgProps} />;
  }

  return (
    <picture>
      <source type="image/webp" srcSet={webpSrcSet} sizes={sizes} />
      <img {...imgProps} />
    </picture>
  );
}
