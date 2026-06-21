"use client";

import { useDelete } from "@/components/dataTable/blackList/api";
import { Button } from "@/components/ui/button";
import type { blackList } from "./type";

type Props = {
  data: blackList;
};

export const Actions = ({ data }: Props) => {
  const deleteMutation = useDelete();

  return <Button onClick={() => deleteMutation.mutate(data.id)}>Delete</Button>;
};
