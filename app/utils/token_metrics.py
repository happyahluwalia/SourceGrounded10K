import time
import tiktoken
from typing import Dict, List, Union
from contextvars import ContextVar


def count_tokens(text: Union[str, List], model: str) -> int:
    """Count tokens in text or list of messages for given model."""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    
    if isinstance(text, str):
        return len(enc.encode(text))
    elif isinstance(text, list):
        # Handle list of messages (e.g., [SystemMessage, HumanMessage])
        total = 0
        for msg in text:
            if hasattr(msg, 'content'):
                total += len(enc.encode(msg.content))
            elif isinstance(msg, dict) and 'content' in msg:
                total += len(enc.encode(msg['content']))
        return total
    return 0


def count_tokens_by_role(messages: List, model: str) -> Dict[str, int]:
    """Count tokens separately for system and human messages."""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    
    system_tokens = 0
    human_tokens = 0
    
    for msg in messages:
        if hasattr(msg, 'content'):
            token_count = len(enc.encode(msg.content))
            # Check message type
            msg_type = type(msg).__name__
            if 'System' in msg_type:
                system_tokens += token_count
            elif 'Human' in msg_type:
                human_tokens += token_count
            else:
                # Default to human for unknown types
                human_tokens += token_count
        elif isinstance(msg, dict) and 'content' in msg:
            token_count = len(enc.encode(msg['content']))
            role = msg.get('role', 'human')
            if role == 'system':
                system_tokens += token_count
            else:
                human_tokens += token_count
    
    return {
        'system': system_tokens,
        'human': human_tokens,
        'total': system_tokens + human_tokens
    }


class TokenMetrics:
    """Track token usage and latency for LLM calls."""
    def __init__(self):
        self.metrics = []
    
    def log_call(
        self,
        stage: str,
        model: str,
        input_messages: List,
        output: str,
        start_time: float,
        end_time: float
    ):
        # Count tokens by role
        input_breakdown = count_tokens_by_role(input_messages, model)
        output_tokens = count_tokens(output, model)
        latency = end_time - start_time
        
        metric_entry = {
            "stage": stage,
            "model": model,
            "input_tokens": {
                "system": input_breakdown['system'],
                "human": input_breakdown['human'],
                "total": input_breakdown['total']
            },
            "output_tokens": output_tokens,
            "latency": round(latency, 2)
        }
        
        self.metrics.append(metric_entry)
        
        # Log immediately for real-time visibility
        import logging
        logger = logging.getLogger(__name__)
        logger.info("="*80)
        logger.info(f" LLM Call: {stage.upper()}")
        logger.info(f" Model: {model}")
        logger.info(f" Input Tokens:")
        logger.info(f"   - System: {input_breakdown['system']}")
        logger.info(f"   - Human: {input_breakdown['human']}")
        logger.info(f"   - Total: {input_breakdown['total']}")
        logger.info(f" Output Tokens: {output_tokens}")
        logger.info(f" Latency: {latency:.2f}s")
        logger.info("="*80)
    
    def get_summary(self) -> Dict:
        """Return aggregated token statistics with detailed breakdown."""
        total_system_tokens = sum(m['input_tokens']['system'] for m in self.metrics)
        total_human_tokens = sum(m['input_tokens']['human'] for m in self.metrics)
        total_input_tokens = sum(m['input_tokens']['total'] for m in self.metrics)
        total_output_tokens = sum(m['output_tokens'] for m in self.metrics)
        total_latency = sum(m['latency'] for m in self.metrics)
        
        return {
            "total_input_tokens": {
                "system": total_system_tokens,
                "human": total_human_tokens,
                "total": total_input_tokens
            },
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "total_latency": round(total_latency, 2),
            "stages": self.metrics
        }
    
    def print_summary(self):
        """Print formatted summary of token usage and performance."""
        import logging
        logger = logging.getLogger(__name__)
        
        summary = self.get_summary()
        
        logger.info("\n" + "="*80)
        logger.info(" TOKEN USAGE & PERFORMANCE ANALYSIS")
        logger.info("="*80)
        
        # Overall totals
        logger.info("\n OVERALL TOTALS:")
        logger.info(f"  Total Input Tokens:")
        logger.info(f"    - System: {summary['total_input_tokens']['system']:,}")
        logger.info(f"    - Human: {summary['total_input_tokens']['human']:,}")
        logger.info(f"    - Total: {summary['total_input_tokens']['total']:,}")
        logger.info(f"  Total Output Tokens: {summary['total_output_tokens']:,}")
        logger.info(f"  Grand Total Tokens: {summary['total_tokens']:,}")
        logger.info(f"  Total Latency: {summary['total_latency']:.2f}s")
        
        # Per-stage breakdown
        logger.info("\n PER-STAGE BREAKDOWN:")
        for i, stage in enumerate(summary['stages'], 1):
            logger.info(f"\n  {i}. {stage['stage'].upper()} ({stage['model']})")
            logger.info(f"     Input:  System={stage['input_tokens']['system']:,}, Human={stage['input_tokens']['human']:,}, Total={stage['input_tokens']['total']:,}")
            logger.info(f"     Output: {stage['output_tokens']:,}")
            logger.info(f"     Time:   {stage['latency']:.2f}s")
        
        # Optimization insights
        logger.info("\n OPTIMIZATION INSIGHTS:")
        if summary['stages']:
            # Find slowest stage
            slowest = max(summary['stages'], key=lambda x: x['latency'])
            logger.info(f"  Slowest stage: {slowest['stage']} ({slowest['latency']:.2f}s)")
            
            # Find most token-heavy stage
            heaviest = max(summary['stages'], key=lambda x: x['input_tokens']['total'] + x['output_tokens'])
            total_tokens_heaviest = heaviest['input_tokens']['total'] + heaviest['output_tokens']
            logger.info(f"  Most token-heavy: {heaviest['stage']} ({total_tokens_heaviest:,} tokens)")
            
            # System prompt optimization opportunity
            if summary['total_input_tokens']['system'] > summary['total_input_tokens']['human']:
                logger.info(f"  System prompts are larger than user queries - consider optimization")
        
        logger.info("\n" + "="*80 + "\n")


# Context variable for token metrics
current_token_metrics: ContextVar[TokenMetrics] = ContextVar('token_metrics', default=None)
