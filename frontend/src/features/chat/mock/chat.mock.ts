/**
 * Mock Chat Service
 * Simulates streaming chat responses with sources
 */

import { ChatMessage, SourceReference, GlobalChatResponse, QuestionResponse } from '../../../api/types'
import { mockSources } from '../../documents/mock/documents.mock'

// Mock responses for different question types
const mockAnswers: Record<string, string> = {
  stoichiometry: `Stoichiometry is the quantitative relationship between reactants and products in a chemical reaction. It's based on the law of conservation of mass, which states that matter cannot be created or destroyed in a chemical reaction.

**Key Concepts:**
1. **Mole Ratio**: The ratio of moles of one substance to moles of another in a balanced equation
2. **Limiting Reactant**: The reactant that is completely consumed first, limiting the amount of product formed
3. **Theoretical Yield**: The maximum amount of product that can be formed from given reactants

**Example Calculation:**
For the reaction: 2H₂ + O₂ → 2H₂O
- 2 moles of hydrogen react with 1 mole of oxygen to produce 2 moles of water
- The mole ratio of H₂ to O₂ is 2:1

To solve stoichiometry problems, always start by writing a balanced chemical equation, then use dimensional analysis with mole ratios to convert between quantities.`,

  organic: `Functional groups are specific groups of atoms within molecules that are responsible for the characteristic chemical reactions of those molecules. Understanding functional groups is fundamental to organic chemistry.

**Common Functional Groups:**
1. **Hydroxyl (-OH)**: Found in alcohols, polar and forms hydrogen bonds
2. **Carbonyl (C=O)**: 
   - Aldehydes (R-CHO): carbonyl at end of chain
   - Ketones (R-CO-R'): carbonyl in middle of chain
3. **Carboxyl (-COOH)**: Found in carboxylic acids, acidic properties
4. **Amino (-NH₂)**: Found in amines, basic properties
5. **Ester (-COO-)**: Sweet-smelling, formed from alcohols and acids

**Nomenclature Rules:**
- Identify the longest carbon chain
- Number the chain from the end nearest the functional group
- Name substituents and their positions
- Use appropriate suffix for the functional group (e.g., -ol for alcohols, -al for aldehydes)`,

  thermodynamics: `Thermodynamics deals with energy changes in chemical reactions. The key concepts include enthalpy, entropy, and Gibbs free energy.

**First Law of Thermodynamics:**
Energy cannot be created or destroyed, only transferred or transformed. ΔU = q + w

**Enthalpy (ΔH):**
- Measure of heat energy in a system at constant pressure
- Exothermic reactions: ΔH < 0 (release heat)
- Endothermic reactions: ΔH > 0 (absorb heat)

**Entropy (ΔS):**
- Measure of disorder or randomness in a system
- Nature tends toward increased entropy
- ΔS > 0 for processes that increase disorder

**Gibbs Free Energy (ΔG):**
ΔG = ΔH - TΔS
- ΔG < 0: Spontaneous reaction
- ΔG > 0: Non-spontaneous reaction
- ΔG = 0: System at equilibrium

**Kinetics vs Thermodynamics:**
- Thermodynamics tells us IF a reaction will occur
- Kinetics tells us HOW FAST it will occur`,

  electrochemistry: `Electrochemistry studies the relationship between electrical energy and chemical reactions, particularly oxidation-reduction (redox) reactions.

**Key Concepts:**
1. **Oxidation**: Loss of electrons (increase in oxidation state)
2. **Reduction**: Gain of electrons (decrease in oxidation state)
3. **Oxidizing Agent**: Substance that gets reduced (causes oxidation)
4. **Reducing Agent**: Substance that gets oxidized (causes reduction)

**Galvanic (Voltaic) Cells:**
- Convert chemical energy to electrical energy
- Spontaneous redox reactions (ΔG < 0, E°cell > 0)
- Anode (oxidation) is negative terminal
- Cathode (reduction) is positive terminal

**Cell Potential:**
E°cell = E°cathode - E°anode

**Nernst Equation:**
E = E° - (RT/nF)lnQ
At 25°C: E = E° - (0.0592/n)logQ

**Applications:**
- Batteries (energy storage)
- Electrolysis (non-spontaneous reactions driven by external voltage)
- Corrosion prevention
- Electroplating`,

  default: `Based on the context from your documents, here's a comprehensive answer to your question.

**Overview:**
The concepts you're studying are interconnected and build upon fundamental chemical principles. Understanding these relationships is crucial for mastering IB Chemistry.

**Key Points:**
1. Start with fundamental definitions and terminology
2. Understand the underlying principles and theories
3. Practice applying concepts to problems
4. Connect related topics across different units

**Study Tips:**
- Create concept maps linking related ideas
- Work through practice problems systematically
- Review the data booklet for important equations and constants
- Focus on understanding WHY, not just memorizing facts

**Common Exam Questions:**
- Definition and explanation questions (recall and understanding)
- Calculation problems (application)
- Analysis and evaluation questions (higher-order thinking)

Remember to always show your work in calculations and use appropriate significant figures!`,
}

export class MockChatService {
  async askQuestion(
    contentId: string,
    question: string,
    userId: string
  ): Promise<AsyncGenerator<string, void, unknown>> {
    // Determine which mock answer to use based on question keywords
    const answer = this.selectAnswer(question)

    return this.streamText(answer)
  }

  async askQuestionComplete(
    contentId: string,
    question: string,
    userId: string
  ): Promise<QuestionResponse> {
    // Simulate API delay
    await this.delay(800)

    const answer = this.selectAnswer(question)

    return {
      question_id: `q-${Date.now()}`,
      content_id: contentId,
      question,
      answer,
      sources: mockSources.slice(0, 3),
      metadata: {
        chunks_used: 5,
        response_time_ms: 2430,
        llm_time_ms: 2100,
        tokens_used: {
          prompt_tokens: 1250,
          completion_tokens: 385,
          total_tokens: 1635,
        },
        model: 'gpt-4-0613',
      },
      cached: Math.random() < 0.3, // 30% chance of cached response
    }
  }

  async askGlobalQuestion(
    question: string,
    userId: string,
    selectedDocIds?: string[]
  ): Promise<AsyncGenerator<string, void, unknown>> {
    const answer = this.selectAnswer(question, true)
    return this.streamText(answer)
  }

  async askGlobalQuestionComplete(
    question: string,
    userId: string,
    selectedDocIds?: string[]
  ): Promise<GlobalChatResponse> {
    await this.delay(1000)

    const answer = this.selectAnswer(question, true)

    // Mix sources from multiple documents for global search
    const globalSources: SourceReference[] = [
      mockSources[0],
      {
        source_id: 4,
        document_title: 'Thermodynamics and Kinetics',
        uploader_name: 'Peter Parker',
        uploader_id: 'user-002',
        upload_date: '2025-10-28',
        chunk_index: 34,
        similarity_score: 0.88,
      },
      {
        source_id: 5,
        document_title: 'Electrochemistry Essentials',
        uploader_name: 'Diana Prince',
        uploader_id: 'user-003',
        upload_date: '2025-10-25',
        chunk_index: 19,
        similarity_score: 0.85,
      },
      mockSources[2],
    ]

    return {
      question_id: `global-q-${Date.now()}`,
      question,
      answer,
      sources: selectedDocIds && selectedDocIds.length > 0 ? mockSources.slice(0, 2) : globalSources,
      metadata: {
        chunks_used: 8,
        documents_searched: selectedDocIds ? selectedDocIds.length : 6,
        response_time_ms: 3250,
        llm_time_ms: 2800,
        tokens_used: {
          prompt_tokens: 2100,
          completion_tokens: 420,
          total_tokens: 2520,
        },
        model: 'gpt-4-0613',
      },
      cached: false,
    }
  }

  private async *streamText(text: string): AsyncGenerator<string, void, unknown> {
    // Split text into words and stream them with realistic delays
    const words = text.split(' ')
    
    for (let i = 0; i < words.length; i++) {
      const word = words[i]
      const delay = Math.random() * 40 + 30 // 30-70ms between words
      
      await this.delay(delay)
      
      // Add space before word (except first word)
      yield i === 0 ? word : ` ${word}`
    }
  }

  private selectAnswer(question: string, isGlobal = false): string {
    const questionLower = question.toLowerCase()

    if (questionLower.includes('stoichiometry') || questionLower.includes('mole')) {
      return mockAnswers.stoichiometry
    }
    if (
      questionLower.includes('organic') ||
      questionLower.includes('functional group') ||
      questionLower.includes('nomenclature')
    ) {
      return mockAnswers.organic
    }
    if (
      questionLower.includes('thermodynamic') ||
      questionLower.includes('enthalpy') ||
      questionLower.includes('entropy')
    ) {
      return mockAnswers.thermodynamics
    }
    if (
      questionLower.includes('electro') ||
      questionLower.includes('redox') ||
      questionLower.includes('oxidation')
    ) {
      return mockAnswers.electrochemistry
    }

    // For global questions, provide a synthesized answer
    if (isGlobal) {
      return `Based on your complete knowledge base of ${Math.floor(Math.random() * 3) + 4} documents, here's a comprehensive answer:

${mockAnswers.default}

**Cross-Document Insights:**
Your documents cover several interconnected topics:
- Stoichiometry forms the foundation for quantitative analysis
- Thermodynamics explains why reactions occur
- Kinetics explains how fast they occur
- Electrochemistry combines these concepts in redox reactions

**Recommended Study Path:**
1. Master stoichiometry calculations first
2. Understand energy changes (thermodynamics)
3. Study reaction mechanisms and rates (kinetics)
4. Apply to electrochemistry and organic reactions

This integrated approach will help you see the bigger picture in chemistry!`
    }

    return mockAnswers.default
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  // Convert chat history to messages
  formatChatHistory(history: ChatMessage[]): ChatMessage[] {
    return history.map((msg) => ({
      ...msg,
      timestamp: msg.timestamp || new Date().toISOString(),
    }))
  }
}

// Export singleton instance
export const mockChatService = new MockChatService()

