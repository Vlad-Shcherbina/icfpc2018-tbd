#pragma once

#include <ostream>
#include <vector>
#include <array>
#include <map>
#include <unordered_map>
#include <set>
#include <utility>
#include <tuple>


// I'm not even sure why this shadowing seems to work.
// Also, there is a risk that libraries relying on old behavior will break.
// But it's convenient for debug output.
static std::ostream& operator<<(std::ostream &out, const std::string &s) {
    out << '"';
    for (char c : s) {
        switch (c) {
            case '\n': out << "\\n"; break;
            case '\"': out << "\\\""; break;
            default: out << c; break;
        }
    }
    out << '"';
    return out;
}


template<typename T>
std::ostream& operator<<(std::ostream &out, const std::vector<T> &v);
template<typename T, size_t size>
std::ostream& operator<<(std::ostream &out, const std::array<T, size> &v);
template<typename T>
std::ostream& operator<<(std::ostream &out, const std::set<T> &s);
template<typename K, typename V>
std::ostream& operator<<(std::ostream &out, const std::map<K, V> &m);
template<typename K, typename V>
std::ostream& operator<<(std::ostream &out, const std::unordered_map<K, V> &m);
template<typename T1, typename T2>
std::ostream& operator<<(std::ostream &out, const std::pair<T1, T2> &p);
template<typename... ElemTypes>
std::ostream& operator<<(std::ostream &out, const std::tuple<ElemTypes...> &t);


template<typename T>
std::ostream& operator<<(std::ostream &out, const std::vector<T> &v) {
  out << "[";
  bool first = true;
  for (const auto &e : v) {
    if (!first)
      out << ", ";
    first = false;
    out << e;
  }
  out << "]";
  return out;
}

template<typename T, size_t size>
std::ostream& operator<<(std::ostream &out, const std::array<T, size> &v) {
  out << "[";
  bool first = true;
  for (const auto &e : v) {
    if (!first)
      out << ", ";
    first = false;
    out << e;
  }
  out << "]";
  return out;
}

template<typename T>
std::ostream& operator<<(std::ostream &out, const std::set<T> &s) {
  out << "{";
  bool first = true;
  for (const auto &e : s) {
    if (!first)
      out << ", ";
    first = false;
    out << e;
  }
  out << "}";
  return out;
}

template<typename K, typename V>
std::ostream& operator<<(std::ostream &out, const std::map<K, V> &m) {
  out << "{";
  bool first = true;
  for (const auto &kv : m) {
    if (!first)
      out << ", ";
    first = false;
    out << kv.first << ": " << kv.second;
  }
  out << "}";
  return out;
}

template<typename K, typename V>
std::ostream& operator<<(std::ostream &out, const std::unordered_map<K, V> &m) {
  out << "{";
  bool first = true;
  for (const auto &kv : m) {
    if (!first)
      out << ", ";
    first = false;
    out << kv.first << ": " << kv.second;
  }
  out << "}";
  return out;
}

template<typename T1, typename T2>
std::ostream& operator<<(std::ostream &out, const std::pair<T1, T2> &p) {
  out << "(" << p.first << ", " << p.second << ")";
  return out;
}


// Tuple operations are messy.

template<int prefix_size, typename... ElemTypes>
struct _print_tuple_elems {
  static void call(std::ostream &out, const std::tuple<ElemTypes...> &t) {
    _print_tuple_elems<prefix_size - 1, ElemTypes...>::call(out, t);
    out << ", " << std::get<prefix_size - 1>(t);
  }
};

template<typename... ElemTypes>
struct _print_tuple_elems<1, ElemTypes...> {
  static void call(std::ostream &out, const std::tuple<ElemTypes...> &t) {
    out << std::get<0>(t);
  }
};

template<typename... ElemTypes>
struct _print_tuple_elems<0, ElemTypes...> {
  static void call(std::ostream &out, const std::tuple<ElemTypes...> &t) {
    (void)out; (void)t;  // suppress unused parameter warning
  }
};

template<typename... ElemTypes>
std::ostream& operator<<(std::ostream &out, const std::tuple<ElemTypes...> &t) {
  out << "(";
  _print_tuple_elems<
      std::tuple_size<std::tuple<ElemTypes...>>::value,
      ElemTypes...>::call(out, t);
  out << ")";
  return out;
}
