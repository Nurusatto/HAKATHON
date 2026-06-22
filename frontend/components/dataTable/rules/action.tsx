import { Button } from "@/components/ui/button";
import { Rules } from "./type";
import { useToggleActive } from "./api";

type Props = {
  data: Rules;
};

export const Actions = ({ data }: Props) => {
  const toggle = useToggleActive();
  console.log(data);
  return (
    <div className="">
      <Button
        onClick={() =>
          toggle.mutate({ id: data.id, isActive: !data.is_active })
        }
      >
        {data.is_active ? "off" : "on"}
      </Button>
    </div>
  );
};
