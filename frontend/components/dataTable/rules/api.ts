import { useQueryClient, useMutation } from "@tanstack/react-query";
import { createClient } from "@/lib/supabase/client";
import { toast } from "sonner";
import { ToggleActivePayload } from "./type";

export const useToggleActive = () => {
  const supabase = createClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, isActive }: ToggleActivePayload) => {
      const { data, error } = await supabase
        .from("security_rules")
        .update({ is_active: isActive })
        .eq("id", id)
        .select();

      if (error) throw new Error(error.message);

      if (!data || data.length === 0) {
        throw new Error(
          "You do not have permission to modify this rule, or it does not exist",
        );
      }
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rulesList"] });
      toast.success("Succes!");
    },
    onError: (err) => toast(err.message),
  });
};
