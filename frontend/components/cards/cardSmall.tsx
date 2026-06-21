import * as React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface CardSmallProps extends Omit<
  React.ComponentProps<typeof Card>,
  "content"
> {
  title: string;
  description?: string | React.ReactNode;
  content: React.ReactNode;
  footer?: React.ReactNode;
  variant?: "classic" | "minimal";
}

export const CardSmall = ({
  title,
  description,
  content,
  footer,
  variant = "classic",
  className,
  ...props
}: CardSmallProps) => {
  return (
    <Card className={cn("w-full max-w-sm", className)} {...props}>
      <CardHeader className={variant === "minimal" ? "pb-2" : undefined}>
        <CardTitle className="text-base font-semibold">{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>

      <CardContent
        className={cn("text-2xl font-bold", variant === "minimal" && "pt-0")}
      >
        {content}
      </CardContent>

      {footer && variant === "classic" && (
        <CardFooter className="text-xs text-muted-foreground">
          {footer}
        </CardFooter>
      )}
    </Card>
  );
};
