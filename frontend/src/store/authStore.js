import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      agenceActive: null,

      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      setUser: (user) => set({ user, agenceActive: user?.agence ?? null }),
      setAgenceActive: (agenceId) => set({ agenceActive: agenceId }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null, agenceActive: null }),
    }),
    {
      name: 'gestion-moto-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        agenceActive: state.agenceActive,
      }),
    },
  ),
)
