import { useEffect, useState } from "react";
import { UtensilsCrossed, type LucideIcon } from "lucide-react";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";

interface FoodImageProps {
  src?: string;
  alt: string;
  tone: number;
  className?: string;
  iconClassName?: string;
  icon?: LucideIcon;
}

export default function FoodImage({ src, alt, tone, className, iconClassName, icon = UtensilsCrossed }: FoodImageProps) {
  const [failed, setFailed] = useState(false);

  useEffect(() => setFailed(false), [src]);

  if (!src || failed) {
    return (
      <PlaceholderMedia
        tone={tone}
        icon={icon}
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
