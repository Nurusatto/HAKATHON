import { createClient } from "@/lib/supabase/client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AddBlockReq } from "./type";
import { toast } from "sonner";

export const useAddBlock = () => {
  const supabase = createClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: AddBlockReq) => {
      const { data, error } = await supabase
        .from("security_bl")
        .insert([
          {
            value: payload.ip,
            reason: payload.reason,
            is_active: true,
            type: "ip",
          },
        ])
        .select();

      if (error) throw new Error(error.message);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["blacklist"] });
    },
    onError: (err) => toast(err.message),
  });
};
