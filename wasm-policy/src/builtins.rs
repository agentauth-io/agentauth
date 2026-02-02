//! Built-in functions for policy evaluation

use std::collections::HashMap;
use std::net::Ipv4Addr;
use hmac::{Hmac, Mac};
use sha2::{Sha256, Digest};

use crate::types::Value;

/// Collection of built-in functions available in policy rules
pub struct BuiltinFunctions;

impl BuiltinFunctions {
    /// Hash a value using SHA-256
    pub fn sha256(input: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(input.as_bytes());
        hex::encode(hasher.finalize())
    }

    /// Compute HMAC-SHA256
    pub fn hmac_sha256(key: &[u8], message: &str) -> String {
        type HmacSha256 = Hmac<Sha256>;
        let mut mac = HmacSha256::new_from_slice(key)
            .expect("HMAC can take key of any size");
        mac.update(message.as_bytes());
        hex::encode(mac.finalize().into_bytes())
    }

    /// Verify HMAC signature
    pub fn verify_hmac(key: &[u8], message: &str, signature: &str) -> bool {
        let expected = Self::hmac_sha256(key, message);
        // Constant-time comparison
        Self::constant_time_eq(expected.as_bytes(), signature.as_bytes())
    }

    /// Constant-time string comparison
    fn constant_time_eq(a: &[u8], b: &[u8]) -> bool {
        if a.len() != b.len() {
            return false;
        }
        let mut result = 0u8;
        for (x, y) in a.iter().zip(b.iter()) {
            result |= x ^ y;
        }
        result == 0
    }

    /// Check if an IP address is in a CIDR range
    pub fn ip_in_cidr(ip: &str, cidr: &str) -> bool {
        let parts: Vec<&str> = cidr.split('/').collect();
        if parts.len() != 2 {
            return false;
        }

        let network = match parts[0].parse::<Ipv4Addr>() {
            Ok(addr) => addr,
            Err(_) => return false,
        };

        let prefix_len: u32 = match parts[1].parse() {
            Ok(len) if len <= 32 => len,
            _ => return false,
        };

        let ip_addr = match ip.parse::<Ipv4Addr>() {
            Ok(addr) => addr,
            Err(_) => return false,
        };

        let mask = if prefix_len == 0 {
            0
        } else {
            !0u32 << (32 - prefix_len)
        };

        let ip_num = u32::from(ip_addr);
        let network_num = u32::from(network);

        (ip_num & mask) == (network_num & mask)
    }

    /// Check if a value is within business hours (9 AM - 5 PM, Mon-Fri)
    pub fn is_business_hours(hour: u8, day_of_week: u8) -> bool {
        // Day of week: 0 = Sunday, 6 = Saturday
        let is_weekday = day_of_week >= 1 && day_of_week <= 5;
        let is_work_hours = hour >= 9 && hour < 17;
        is_weekday && is_work_hours
    }

    /// Check if time is within a specified range
    pub fn time_in_range(hour: u8, start: u8, end: u8) -> bool {
        if start <= end {
            hour >= start && hour <= end
        } else {
            // Handle overnight ranges (e.g., 22-6)
            hour >= start || hour <= end
        }
    }

    /// Calculate Levenshtein distance between two strings
    pub fn levenshtein_distance(a: &str, b: &str) -> usize {
        let a_len = a.chars().count();
        let b_len = b.chars().count();

        if a_len == 0 {
            return b_len;
        }
        if b_len == 0 {
            return a_len;
        }

        let mut matrix = vec![vec![0; b_len + 1]; a_len + 1];

        for i in 0..=a_len {
            matrix[i][0] = i;
        }
        for j in 0..=b_len {
            matrix[0][j] = j;
        }

        for (i, a_char) in a.chars().enumerate() {
            for (j, b_char) in b.chars().enumerate() {
                let cost = if a_char == b_char { 0 } else { 1 };
                matrix[i + 1][j + 1] = std::cmp::min(
                    std::cmp::min(
                        matrix[i][j + 1] + 1,     // deletion
                        matrix[i + 1][j] + 1,     // insertion
                    ),
                    matrix[i][j] + cost,          // substitution
                );
            }
        }

        matrix[a_len][b_len]
    }

    /// Check if two strings are similar (fuzzy match)
    pub fn fuzzy_match(a: &str, b: &str, threshold: f64) -> bool {
        let max_len = std::cmp::max(a.len(), b.len());
        if max_len == 0 {
            return true;
        }
        let distance = Self::levenshtein_distance(a, b);
        let similarity = 1.0 - (distance as f64 / max_len as f64);
        similarity >= threshold
    }

    /// Extract domain from email address
    pub fn email_domain(email: &str) -> Option<String> {
        email.split('@').nth(1).map(|s| s.to_lowercase())
    }

    /// Check if email is from a specific domain
    pub fn email_from_domain(email: &str, domain: &str) -> bool {
        Self::email_domain(email)
            .map(|d| d == domain.to_lowercase())
            .unwrap_or(false)
    }

    /// Format a monetary amount
    pub fn format_currency(amount: f64, currency: &str) -> String {
        match currency.to_uppercase().as_str() {
            "USD" => format!("${:.2}", amount),
            "EUR" => format!("€{:.2}", amount),
            "GBP" => format!("£{:.2}", amount),
            "JPY" => format!("¥{:.0}", amount),
            _ => format!("{:.2} {}", amount, currency),
        }
    }

    /// Calculate percentage
    pub fn percentage(value: f64, total: f64) -> f64 {
        if total == 0.0 {
            0.0
        } else {
            (value / total) * 100.0
        }
    }

    /// Check if a list contains a value
    pub fn list_contains(list: &[Value], target: &Value) -> bool {
        list.iter().any(|v| match (v, target) {
            (Value::String(a), Value::String(b)) => a.to_lowercase() == b.to_lowercase(),
            (Value::Int(a), Value::Int(b)) => a == b,
            (Value::Float(a), Value::Float(b)) => (a - b).abs() < f64::EPSILON,
            (Value::Bool(a), Value::Bool(b)) => a == b,
            _ => false,
        })
    }

    /// Check if any element in list1 exists in list2
    pub fn lists_overlap(list1: &[Value], list2: &[Value]) -> bool {
        list1.iter().any(|v| Self::list_contains(list2, v))
    }

    /// Get the intersection of two lists
    pub fn list_intersection(list1: &[Value], list2: &[Value]) -> Vec<Value> {
        list1
            .iter()
            .filter(|v| Self::list_contains(list2, v))
            .cloned()
            .collect()
    }

    /// Parse and validate a UUID
    pub fn is_valid_uuid(s: &str) -> bool {
        let s = s.replace('-', "");
        if s.len() != 32 {
            return false;
        }
        s.chars().all(|c| c.is_ascii_hexdigit())
    }

    /// Get nested value from object
    pub fn get_nested(obj: &HashMap<String, Value>, path: &str) -> Option<Value> {
        let parts: Vec<&str> = path.split('.').collect();
        let mut current: &Value = obj.get(parts[0])?;

        for part in parts.iter().skip(1) {
            match current {
                Value::Object(map) => {
                    current = map.get(*part)?;
                }
                Value::List(list) => {
                    let index: usize = part.parse().ok()?;
                    current = list.get(index)?;
                }
                _ => return None,
            }
        }

        Some(current.clone())
    }

    /// Calculate risk score from multiple factors
    pub fn calculate_risk_score(factors: &[(String, f64, f64)]) -> f64 {
        // factors: (name, value, weight)
        let total_weight: f64 = factors.iter().map(|(_, _, w)| w).sum();
        if total_weight == 0.0 {
            return 0.0;
        }

        let weighted_sum: f64 = factors
            .iter()
            .map(|(_, value, weight)| value * weight)
            .sum();

        (weighted_sum / total_weight).clamp(0.0, 1.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sha256() {
        let hash = BuiltinFunctions::sha256("hello");
        assert_eq!(
            hash,
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        );
    }

    #[test]
    fn test_ip_in_cidr() {
        assert!(BuiltinFunctions::ip_in_cidr("192.168.1.100", "192.168.1.0/24"));
        assert!(!BuiltinFunctions::ip_in_cidr("192.168.2.100", "192.168.1.0/24"));
        assert!(BuiltinFunctions::ip_in_cidr("10.0.0.1", "10.0.0.0/8"));
    }

    #[test]
    fn test_is_business_hours() {
        assert!(BuiltinFunctions::is_business_hours(10, 1)); // 10 AM Monday
        assert!(!BuiltinFunctions::is_business_hours(10, 0)); // 10 AM Sunday
        assert!(!BuiltinFunctions::is_business_hours(20, 1)); // 8 PM Monday
    }

    #[test]
    fn test_fuzzy_match() {
        assert!(BuiltinFunctions::fuzzy_match("hello", "helo", 0.8));
        assert!(!BuiltinFunctions::fuzzy_match("hello", "world", 0.8));
    }

    #[test]
    fn test_email_domain() {
        assert_eq!(
            BuiltinFunctions::email_domain("user@example.com"),
            Some("example.com".to_string())
        );
    }
}
