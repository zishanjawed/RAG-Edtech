import { AnimatePresence, motion } from 'framer-motion'
import React from 'react'

export interface PageTransitionProps {
  children: React.ReactNode
  routeKey: string
}

export function PageTransition({ children, routeKey }: PageTransitionProps) {
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={routeKey}
        initial={{ opacity: 0, y: 10, filter: 'blur(4px)' }}
        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
        exit={{ opacity: 0, y: -10, filter: 'blur(4px)' }}
        transition={{ 
          duration: 0.25, 
          ease: [0.22, 1, 0.36, 1] // easeOutExpo
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}


