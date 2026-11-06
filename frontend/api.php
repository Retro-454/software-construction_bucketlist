<?php
// api.php: the only way the PHP frontend talks to the backend.
// Pages call api(); it sends the request to the Flask API with the
// logged-in user's id in X-Actor-Id, and returns the decoded JSON.
// Never query the database from PHP directly: that skips the permission checks.

const API_BASE = 'http://127.0.0.1:5000/api';

class ApiError extends Exception {}   // message = backend {"error": ...}, code = HTTP status

function api(string $method, string $path, ?array $data = null) {
    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_start();
    }
    $headers = ['Accept: application/json'];
    if (isset($_SESSION['user_id'])) {
        $headers[] = 'X-Actor-Id: ' . (int) $_SESSION['user_id'];
    }
    $ch = curl_init(API_BASE . $path);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    if ($data !== null) {
        $headers[] = 'Content-Type: application/json';
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    }
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    $raw = curl_exec($ch);
    $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlError = curl_error($ch);
    curl_close($ch);

    if ($raw === false) {
        throw new ApiError('Backend not reachable: ' . $curlError, 503);
    }
    $json = json_decode($raw, true);
    if ($status >= 400) {
        throw new ApiError($json['error'] ?? 'Request failed', $status);
    }
    return $json;
}
