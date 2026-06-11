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
  if (!avifSrcSet || !webpSrcSet) {
    return <img {...imgProps} />;
  }

  return (
    <picture>
      <source type="image/avif" srcSet={avifSrcSet} sizes={sizes} />
      <source type="image/webp" srcSet={webpSrcSet} sizes={sizes} />
      <img {...imgProps} />
    </picture>
  );
}
