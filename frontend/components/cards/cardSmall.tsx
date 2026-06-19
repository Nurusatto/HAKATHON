import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type CardProps = {
  header: string;
  description: string;
  content: string | number;
};

type prop = {
  obj: CardProps;
};

export const CardSmall = ({ obj }: prop) => {
  return (
    <Card size="sm" className="mx-auto w-full max-w-sm">
      <CardHeader>
        <CardTitle>{obj.header}</CardTitle>
        <CardDescription>{obj.description}</CardDescription>
      </CardHeader>
      <CardContent>{obj.content}</CardContent>
      <CardFooter></CardFooter>
    </Card>
  );
};
