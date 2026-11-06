<?php

declare(strict_types=1);

namespace EarlyForge\Pulse;

final class PulseApiException extends \RuntimeException
{
    /**
     * @param array<string, mixed>|string|null $detail Structured on the
     *   full-trends endpoints (e.g. upgrade_required/trend_locked), a
     *   plain string elsewhere.
     */
    public function __construct(
        string $message,
        private readonly ?int $statusCode = null,
        private readonly array|string|null $detail = null,
    ) {
        parent::__construct($message);
    }

    public function getStatusCode(): ?int
    {
        return $this->statusCode;
    }

    /** @return array<string, mixed>|string|null */
    public function getDetail(): array|string|null
    {
        return $this->detail;
    }
}
