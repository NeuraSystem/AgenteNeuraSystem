interface ElevenLabsConfig {
  apiKey: string;
  baseUrl: string;
  defaultVoiceId: string;
}

interface VoiceSettings {
  stability: number;
  similarity_boost: number;
  style?: number;
  use_speaker_boost?: boolean;
}

interface TextToSpeechRequest {
  text: string;
  voice_id?: string;
  voice_settings?: VoiceSettings;
  pronunciation_dictionary_locators?: string[];
  seed?: number;
  previous_text?: string;
  next_text?: string;
  previous_request_ids?: string[];
  next_request_ids?: string[];
}

interface TextToSpeechResponse {
  audio_url?: string;
  audio_blob?: Blob;
  alignment?: any;
  normalized_alignment?: any;
}

export class ElevenLabsService {
  private config: ElevenLabsConfig;
  private audioCache: Map<string, Blob> = new Map();
  private backendUrl: string;

  constructor(apiKey: string) {
    this.config = {
      apiKey,
      baseUrl: 'https://api.elevenlabs.io',
      defaultVoiceId: '21m00Tcm4TlvDq8ikWAM' // Rachel voice - natural female
    };
    this.backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  }

  /**
   * Converts text to speech using backend proxy with emotional and natural controls
   */
  async textToSpeech(
    text: string, 
    options: Partial<TextToSpeechRequest> = {}
  ): Promise<Blob> {
    const cacheKey = this.getCacheKey(text, options);
    
    // Check local cache first
    if (this.audioCache.has(cacheKey)) {
      return this.audioCache.get(cacheKey)!;
    }

    // Detect emotional context for better voice settings
    const emotionalContext = this.detectEmotionalContext(text);

    const request = {
      text,
      voice_id: options.voice_id || this.config.defaultVoiceId,
      voice_settings: options.voice_settings,
      model_id: 'eleven_turbo_v2',
      emotional_context: emotionalContext,
      stream: false // Explicitly false for this method
    };

    try {
      // Use backend proxy for better caching and security
      const response = await fetch(`${this.backendUrl}/voice/text-to-speech`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`Backend TTS error: ${response.status} - ${errorText}`);
      }

      const audioBlob = await response.blob();
      
      // Cache the result locally
      this.audioCache.set(cacheKey, audioBlob);
      
      // Clean cache if it gets too large
      if (this.audioCache.size > 30) {
        const firstKey = this.audioCache.keys().next().value;
        this.audioCache.delete(firstKey);
      }

      return audioBlob;
    } catch (error) {
      console.error('TTS Error:', error);
      
      // Fallback to Web Speech API if backend fails
      return this.fallbackToWebSpeech(text);
    }
  }

  /**
   * Converts text to speech using backend proxy and streams the audio.
   */
  async textToSpeechStream(
    text: string,
    options: Partial<TextToSpeechRequest> = {},
    onStreamChunk: (chunk: Uint8Array) => void,
    onStreamEnd: () => void,
    onStreamError: (error: Error) => void
  ): Promise<void> {
    const emotionalContext = this.detectEmotionalContext(text);

    const request = {
      text,
      voice_id: options.voice_id || this.config.defaultVoiceId,
      voice_settings: options.voice_settings,
      model_id: 'eleven_turbo_v2',
      emotional_context: emotionalContext,
      stream: true // Explicitly true for this method
    };

    try {
      const response = await fetch(`${this.backendUrl}/voice/text-to-speech`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(request)
      });

      if (!response.ok || !response.body) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`Backend TTS streaming error: ${response.status} - ${errorText}`);
      }

      const reader = response.body.getReader();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          onStreamEnd();
          break;
        }
        if (value) {
          onStreamChunk(value);
        }
      }
    } catch (error) {
      console.error('TTS Streaming Error:', error);
      onStreamError(error instanceof Error ? error : new Error('Unknown streaming error'));
    }
  }

  /**
   * Fallback to browser Web Speech API if ElevenLabs fails
   */
  private async fallbackToWebSpeech(text: string): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!('speechSynthesis' in window)) {
        reject(new Error('Speech synthesis not supported'));
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'es-ES';
      utterance.rate = 0.9;
      utterance.pitch = 1.0;

      // Find Spanish voice if available
      const voices = speechSynthesis.getVoices();
      const spanishVoice = voices.find(voice => voice.lang.startsWith('es'));
      if (spanishVoice) {
        utterance.voice = spanishVoice;
      }

      utterance.onend = () => {
        // Web Speech API doesn't provide audio blob directly
        // Return empty blob as placeholder - audio will play directly
        resolve(new Blob());
      };

      utterance.onerror = (error) => {
        reject(new Error(`Web Speech API error: ${error.error}`));
      };

      speechSynthesis.speak(utterance);
    });
  }

  /**
   * Enhances text with natural speech controls and emotional markers
   */
  private enhanceTextForNaturalSpeech(text: string): string {
    let enhanced = text;

    // Add natural pauses after punctuation
    enhanced = enhanced.replace(/([.!?])\s+/g, '$1<break time="0.5s"/> ');
    enhanced = enhanced.replace(/([,;:])\s+/g, '$1<break time="0.3s"/> ');

    // Add emphasis for certain patterns
    enhanced = enhanced.replace(/\*\*(.*?)\*\*/g, '<emphasis level="strong">$1</emphasis>');
    enhanced = enhanced.replace(/\*(.*?)\*/g, '<emphasis level="moderate">$1</emphasis>');

    // Add emotional context for questions and exclamations
    if (enhanced.includes('?')) {
      enhanced = `<prosody rate="1.0" pitch="medium">${enhanced}</prosody>`;
    }
    
    if (enhanced.includes('!')) {
      enhanced = enhanced.replace(/([^!]+!)/g, '<prosody rate="1.1" pitch="high">$1</prosody>');
    }

    // Handle technical terms that might need pronunciation help
    const technicalTerms: Record<string, string> = {
      'API': '<phoneme alphabet="ipa" ph="eɪ piː aɪ">API</phoneme>',
      'HTTP': '<phoneme alphabet="ipa" ph="eɪtʃ tiː tiː piː">HTTP</phoneme>',
      'JSON': '<phoneme alphabet="ipa" ph="dʒeɪsən">JSON</phoneme>',
      'URL': '<phoneme alphabet="ipa" ph="juː ɑr ɛl">URL</phoneme>',
      'ChatIng': '<phoneme alphabet="ipa" ph="tʃæt ɪŋ">ChatIng</phoneme>',
      'SQL': '<phoneme alphabet="ipa" ph="ɛs kjuː ɛl">SQL</phoneme>'
    };

    Object.entries(technicalTerms).forEach(([term, pronunciation]) => {
      const regex = new RegExp(`\\b${term}\\b`, 'gi');
      enhanced = enhanced.replace(regex, pronunciation);
    });

    return enhanced;
  }

  /**
   * Adjusts voice settings for different emotional contexts
   */
  getVoiceSettingsForContext(context: 'helpful' | 'excited' | 'calm' | 'professional' | 'friendly'): VoiceSettings {
    const baseSettings: VoiceSettings = {
      stability: 0.75,
      similarity_boost: 0.85,
      use_speaker_boost: true
    };

    switch (context) {
      case 'excited':
        return {
          ...baseSettings,
          stability: 0.65,
          style: 0.85
        };
      case 'calm':
        return {
          ...baseSettings,
          stability: 0.85,
          style: 0.45
        };
      case 'professional':
        return {
          ...baseSettings,
          stability: 0.80,
          style: 0.55
        };
      case 'friendly':
        return {
          ...baseSettings,
          stability: 0.70,
          style: 0.75
        };
      case 'helpful':
      default:
        return {
          ...baseSettings,
          style: 0.65
        };
    }
  }

  /**
   * Generates a cache key for the request
   */
  private getCacheKey(text: string, options: Partial<TextToSpeechRequest>): string {
    const settingsString = JSON.stringify(options.voice_settings || {});
    const voiceId = options.voice_id || this.config.defaultVoiceId;
    return `${voiceId}_${settingsString}_${text.substring(0, 100)}`;
  }

  /**
   * Clears the audio cache
   */
  clearCache(): void {
    this.audioCache.clear();
  }

  /**
   * Gets available voices from ElevenLabs
   */
  async getVoices(): Promise<any[]> {
    try {
      const response = await fetch(`${this.config.baseUrl}/v1/voices`, {
        headers: {
          'xi-api-key': this.config.apiKey
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch voices: ${response.status}`);
      }

      const data = await response.json();
      return data.voices || [];
    } catch (error) {
      console.error('Error fetching voices:', error);
      return [];
    }
  }

  /**
   * Converts response context to emotional voice setting
   */
  detectEmotionalContext(text: string): 'helpful' | 'excited' | 'calm' | 'professional' | 'friendly' {
    const lowerText = text.toLowerCase();
    
    if (lowerText.includes('error') || lowerText.includes('problema') || lowerText.includes('sorry')) {
      return 'calm';
    }
    
    if (lowerText.includes('!') && (lowerText.includes('genial') || lowerText.includes('perfecto') || lowerText.includes('excelente'))) {
      return 'excited';
    }
    
    if (lowerText.includes('técnico') || lowerText.includes('configuración') || lowerText.includes('código')) {
      return 'professional';
    }
    
    if (lowerText.includes('hola') || lowerText.includes('gracias') || lowerText.includes('bueno')) {
      return 'friendly';
    }
    
    return 'helpful';
  }
}

// Singleton instance
let elevenLabsInstance: ElevenLabsService | null = null;

export const getElevenLabsService = (): ElevenLabsService => {
  if (!elevenLabsInstance) {
    const apiKey = import.meta.env.VITE_ELEVENLABS_API_KEY || 'sk_01cea666c20e2b4d2e4e31907af90c4d016652b8331ed2f1';
    elevenLabsInstance = new ElevenLabsService(apiKey);
  }
  return elevenLabsInstance;
};