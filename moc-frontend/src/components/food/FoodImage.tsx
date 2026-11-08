import { useEffect, useState } from "react";
import { UtensilsCrossed } from "lucide-react";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";

interface FoodImageProps {
  src?: string;
  alt: string;
  tone: number;
  className?: string;
  iconClassName?: string;
}

export default function FoodImage({ src, alt, tone, className, iconClassName }: FoodImageProps) {
  const [failed, setFailed] = useState(false);

  useEffect(() => setFailed(false), [src]);

  if (!src || failed) {
    return (
      <PlaceholderMedia
        tone={tone}
        icon={UtensilsCrossed}
        className={className}
        iconClassName={iconClassName}
      />
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      onError={() => setFailed(true)}
      className={className}
    />
  );
}
