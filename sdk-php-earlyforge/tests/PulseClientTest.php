<?php

declare(strict_types=1);

namespace EarlyForge\Pulse\Tests;

use EarlyForge\Pulse\PulseApiException;
use EarlyForge\Pulse\PulseClient;
use PHPUnit\Framework\TestCase;

final class PulseClientTest extends TestCase
{
    public function testTopTrendsSendsBearerTokenAndBuildsUrl(): void
    {
        $seen = [];
        $client = new PulseClient('ef_live_test', 'https://api.test', function (string $url, array $headers) use (&$seen) {
            $seen[] = ['url' => $url, 'headers' => $headers];
            return ['status' => 200, 'body' => json_encode(['trends' => [], 'total' => 0])];
        });

        $result = $client->topTrends(null, 'fr');

        self::assertSame(['trends' => [], 'total' => 0], $result);
        self::assertCount(1, $seen);
        self::assertContains('Authorization: Bearer ef_live_test', $seen[0]['headers']);
        self::assertStringStartsWith('https://api.test/v1/api/trends/top', $seen[0]['url']);
        self::assertStringContainsString('locale=fr', $seen[0]['url']);
    }

    public function testTrendsByRegionBuildsPathSegment(): void
    {
        $client = new PulseClient('ef_live_test', 'https://api.test', function (string $url, array $headers) {
            self::assertStringContainsString('/v1/api/trends/region/US', $url);
            return ['status' => 200, 'body' => json_encode(['trends' => [], 'total' => 0])];
        });

        $client->trendsByRegion('US');
    }

    public function testGetTrendThrowsPulseApiExceptionOn404(): void
    {
        $client = new PulseClient('ef_live_test', 'https://api.test', function () {
            return ['status' => 404, 'body' => json_encode(['detail' => 'Not found'])];
        });

        try {
            $client->getTrend('tr_missing');
            self::fail('Expected PulseApiException');
        } catch (PulseApiException $exception) {
            self::assertSame(404, $exception->getStatusCode());
            self::assertSame('Not found', $exception->getDetail());
        }
    }

    public function testConstructorRequiresApiKey(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        new PulseClient('');
    }

    public function testFullTrendsReturnsItemsWithTotal(): void
    {
        $client = new PulseClient('ef_live_test', 'https://api.test', function (string $url, array $headers) {
            self::assertStringStartsWith('https://api.test/v1/api/trends/full', $url);
            self::assertStringContainsString('region=US', $url);
            return ['status' => 200, 'body' => json_encode([
                'items' => [['trend_id' => 'tr_1']],
                'total' => 1,
                'page' => 1,
                'per_page' => 20,
            ])];
        });

        $result = $client->fullTrends('US');

        self::assertSame(1, $result['total']);
    }

    public function testFullTrendsThrowsPulseApiExceptionWithStructuredDetailOn402(): void
    {
        $client = new PulseClient('ef_live_test', 'https://api.test', function () {
            return ['status' => 402, 'body' => json_encode([
                'detail' => ['error' => 'upgrade_required', 'upgrade_url' => '/settings/billing'],
            ])];
        });

        try {
            $client->fullTrends();
            self::fail('Expected PulseApiException');
        } catch (PulseApiException $exception) {
            self::assertSame(402, $exception->getStatusCode());
            self::assertSame('upgrade_required', $exception->getDetail()['error']);
        }
    }

    public function testGetFullTrendThrowsPulseApiExceptionOn402TrendLocked(): void
    {
        $client = new PulseClient('ef_live_test', 'https://api.test', function () {
            return ['status' => 402, 'body' => json_encode([
                'detail' => ['error' => 'This trend is locked on your plan', 'code' => 'trend_locked'],
            ])];
        });

        try {
            $client->getFullTrend('tr_locked');
            self::fail('Expected PulseApiException');
        } catch (PulseApiException $exception) {
            self::assertSame('trend_locked', $exception->getDetail()['code']);
        }
    }
}
