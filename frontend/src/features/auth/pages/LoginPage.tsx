/**
 * LoginPage
 * Modern login page with glassmorphism and gradient animations
 */
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { GraduationCap, Sparkles, BookOpen, Zap } from 'lucide-react'
import { LoginForm } from '../components/LoginForm'
import { AnimatedBackground } from '@/components/animated/AnimatedBackground'
import { SpotlightCard } from '@/components/animated/SpotlightCard'
import { TextReveal } from '@/components/animated/TextReveal'
import { cn } from '@/lib/utils'

export function LoginPage() {
  return (
    <div className="relative flex min-h-screen overflow-hidden">
      <AnimatedBackground opacity={0.45} />
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-primary-50/30 to-secondary-50/30">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiM2MzY2ZjEiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDE0YzAtNC40MTggMy41ODItOCA4LThzOCAzLjU4MiA4IDgtMy41ODIgOC04IDgtOC0zLjU4Mi04LTh6TTAgMTRjMC00LjQxOCAzLjU4Mi04IDgtOHM4IDMuNTgyIDggOC0zLjU4MiA4LTggOC04LTMuNTgyLTgtOHoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-40"></div>
      </div>

      {/* Left side - Form */}
      <div className="relative z-10 flex w-full flex-col justify-center px-6 py-12 lg:w-1/2 lg:px-20">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="mx-auto w-full max-w-md"
        >
          {/* Logo with Float Animation */}
          <motion.div
            className="mb-8 text-center"
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            <Link 
              to="/" 
              className="inline-flex items-center gap-2 text-primary-600 transition-transform hover:scale-105"
            >
              <motion.div
                animate={{ rotate: [0, 5, -5, 0] }}
                transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
              >
                <GraduationCap className="h-10 w-10" />
              </motion.div>
              <span className="text-2xl font-bold">RAG Edtech</span>
            </Link>
            
            <TextReveal delayMs={200} className="mt-6">
              <h2 className="text-3xl font-bold text-slate-900 sm:text-4xl">Welcome Back</h2>
            </TextReveal>
            
            <motion.p 
              className="mt-2 text-sm text-slate-600"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              Sign in to continue your learning journey
            </motion.p>
          </motion.div>

          {/* Login Form with Glass Effect */}
          <SpotlightCard className={cn("p-0")}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.5 }}
              className={cn(
                "rounded-2xl border border-slate-200/60 bg-white/80 p-8 shadow-xl backdrop-blur-sm",
                "transition-all duration-300 hover:shadow-2xl"
              )}
            >
              <LoginForm />
            </motion.div>
          </SpotlightCard>

          {/* Register Link */}
          <motion.p 
            className="mt-6 text-center text-sm text-slate-600"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            Don't have an account?{' '}
            <Link 
              to="/register" 
              className="font-medium text-primary-600 transition-colors hover:text-primary-700"
            >
              Sign up
            </Link>
          </motion.p>
        </motion.div>
      </div>

      {/* Right side - Hero with Animated Gradient */}
      <motion.div
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="hidden lg:block lg:w-1/2"
      >
        <div className="relative flex h-full items-center justify-center overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-secondary-600 p-12">
          {/* Animated Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-tr from-primary-600/50 via-transparent to-accent-500/30 animate-gradient bg-[length:200%_auto]"></div>
          
          {/* Floating Shapes */}
          <motion.div
            className="absolute top-20 right-20 h-64 w-64 rounded-full bg-white/5 blur-3xl"
            animate={{ 
              scale: [1, 1.2, 1],
              opacity: [0.3, 0.5, 0.3]
            }}
            transition={{ duration: 8, repeat: Infinity }}
          />
          <motion.div
            className="absolute bottom-20 left-20 h-64 w-64 rounded-full bg-secondary-400/10 blur-3xl"
            animate={{ 
              scale: [1, 1.3, 1],
              opacity: [0.2, 0.4, 0.2]
            }}
            transition={{ duration: 10, repeat: Infinity, delay: 1 }}
          />

          {/* Content */}
          <div className="relative z-10 max-w-md text-white">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.6 }}
            >
              <h3 className="text-4xl font-bold leading-tight sm:text-5xl">
                AI-Powered Learning
              </h3>
              <p className="mt-4 text-lg text-primary-100">
                Get instant answers to your questions with our advanced RAG-based chatbot. Upload your
                study materials and start learning smarter.
              </p>
            </motion.div>

            <div className="mt-10 space-y-5">
              {[
                { icon: Sparkles, title: "Intelligent Q&A", desc: "Ask questions about your documents" },
                { icon: BookOpen, title: "Document Upload", desc: "Support for PDF, TXT, MD, and DOCX" },
                { icon: Zap, title: "Real-time Responses", desc: "Streaming AI-generated answers" }
              ].map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.7 + index * 0.1, duration: 0.5 }}
                  className="flex items-start gap-4 rounded-xl bg-white/5 p-4 backdrop-blur-sm transition-all hover:bg-white/10"
                >
                  <motion.div 
                    className="rounded-xl bg-white/10 p-2.5"
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    <feature.icon className="h-5 w-5" />
                  </motion.div>
                  <div>
                    <h4 className="font-semibold">{feature.title}</h4>
                    <p className="text-sm text-primary-100">{feature.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

