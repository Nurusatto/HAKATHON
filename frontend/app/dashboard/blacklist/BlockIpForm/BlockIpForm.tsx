"use client";

import { useForm, Controller } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import { schema } from "@/app/dashboard/blacklist/BlockIpForm/schema";
import { useAddBlock } from "./api";
import type { AddBlockReq } from "./type";

export const BlockIpForm = () => {
  const useadd = useAddBlock();
  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    resolver: yupResolver(schema),
  });

  const onSubmit = (data: AddBlockReq) => {
    useadd.mutate(data);
    reset();
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="p-4 bg-card border border-border rounded-xl space-y-4 max-w-md shadow-sm font-sans"
    >
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-1">
          Ban Network IP
        </h3>
        <p className="text-[11px] text-muted-foreground">
          Restrict malicious IP address immediately.
        </p>
      </div>

      <div className="space-y-3">
        <div className="space-y-1">
          <label className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
            IP Address
          </label>
          <Controller
            name="ip"
            control={control}
            render={({ field: { onChange, value } }) => (
              <input
                type="text"
                placeholder="192.168.1.1"
                value={value || ""}
                onChange={(e) => {
                  let val = e.target.value;
                  val = val.replace(/[^0-9.]/g, "");
                  val = val.replace(/\.{2,}/g, ".");
                  const parts = val.split(".");
                  if (parts.length > 4) return;
                  const validatedParts = parts.map((part) => {
                    if (part.length > 3) return part.slice(0, 3);
                    if (parseInt(part, 10) > 255) return "255";
                    return part;
                  });

                  onChange(validatedParts.join("."));
                }}
                className={`w-full bg-muted/50 border ${
                  errors.ip
                    ? "border-destructive focus:ring-destructive"
                    : "border-border focus:ring-ring"
                } rounded-md px-3 py-1.5 text-xs font-mono text-foreground outline-none focus:ring-1`}
              />
            )}
          />
          {errors.ip && (
            <p className="text-[11px] text-destructive font-mono">
              {errors.ip.message}
            </p>
          )}
        </div>
        <div className="space-y-1">
          <label className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
            Reason
          </label>
          <input
            type="text"
            placeholder="e.g., Auth Bruteforce"
            {...control.register("reason")}
            className="w-full bg-muted/50 border border-border rounded-md px-3 py-1.5 text-xs text-foreground outline-none focus:ring-1 focus:ring-ring"
          />
          {errors.reason && (
            <p className="text-[11px] text-destructive font-mono">
              {errors.reason.message}
            </p>
          )}
        </div>
      </div>

      <button
        type="submit"
        // disabled={isPending}
        className="w-full px-4 py-2 bg-primary text-primary-foreground text-xs font-medium rounded-md hover:opacity-90 disabled:opacity-50 cursor-pointer font-mono"
      >
        {false ? "EXECUTING BAN..." : "INITIALIZE BAN"}
      </button>
    </form>
  );
};
