"use client";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function AuthSuccess() {
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const token = searchParams.get("token");
    if (token) {
      // 1. Save the token to LocalStorage
      localStorage.setItem("emailing_token", token);
      
      // 2. Clear the URL and send the user to the dashboard
      router.push("/");
    }
  }, [searchParams, router]);

  return (
    <div className="h-screen flex items-center justify-center bg-slate-50">
      <p className="animate-pulse font-bold text-indigo-600">Securely logging you in...</p>
    </div>
  );
}