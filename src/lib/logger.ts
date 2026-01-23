/**
 * Production-safe logger utility
 * 
 * Logs to console only in development mode.
 * In production, errors can be sent to error tracking services.
 */

type LogLevel = 'log' | 'error' | 'warn' | 'info' | 'debug';

class Logger {
    private isDevelopment: boolean;

    constructor() {
        this.isDevelopment = import.meta.env.DEV || import.meta.env.MODE === 'development';
    }

    log(...args: any[]): void {
        if (this.isDevelopment) {
            console.log(...args);
        }
    }

    error(...args: any[]): void {
        if (this.isDevelopment) {
            console.error(...args);
        } else {
            // In production, send to error tracking service
            // Example: Sentry.captureException(args[0]);
            // For now, we silently ignore to prevent console pollution
        }
    }

    warn(...args: any[]): void {
        if (this.isDevelopment) {
            console.warn(...args);
        }
    }

    info(...args: any[]): void {
        if (this.isDevelopment) {
            console.info(...args);
        }
    }

    debug(...args: any[]): void {
        if (this.isDevelopment) {
            console.debug(...args);
        }
    }

    /**
     * Log with context for better debugging
     */
    logWithContext(context: string, level: LogLevel, ...args: any[]): void {
        if (this.isDevelopment) {
            const timestamp = new Date().toISOString();
            console[level](`[${timestamp}] [${context}]`, ...args);
        }
    }
}

// Export singleton instance
export const logger = new Logger();

// Export default for convenience
export default logger;
